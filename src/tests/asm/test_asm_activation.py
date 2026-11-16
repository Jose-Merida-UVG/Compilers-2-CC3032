"""Datos de activación para el IDE: marcos y árbol de llamadas."""

from __future__ import annotations

from antlr4 import InputStream

from asm.generator import generate_asm
from compiler import analyze


def activation(source: str) -> dict:
    result = analyze(InputStream(source))
    assert result["errors"] == [], result["errors"]
    return generate_asm(result["tac"], result["symbol_table_json"]).activation


def find(node: dict, label: str):
    return next((c for c in node["children"] if c["label"] == label), None)


def test_frames_have_slots_from_high_to_low_addresses():
    act = activation(
        "function suma(a: integer, b: integer): integer { let c: integer = a + b; return c; }\n"
        "print(suma(1, 2));\n"
    )
    frame = act["frames"]["suma"]
    assert [s["name"] for s in frame["slots"] if s["kind"] == "param"] == ["b", "a"]  # el último argumento queda en la dirección más alta
    assert {"$ra", "$fp"} <= {s["name"] for s in frame["slots"] if s["kind"] == "saved"}
    offsets = [s["offset"] for s in frame["slots"]]
    assert offsets == sorted(offsets, reverse=True)
    assert frame["total_size"] > 0
    assert "__main" in act["frames"]


def test_tree_starts_at_main_and_lists_calls_in_order():
    act = activation(
        "function f(): integer { return 1; }\nfunction g(): integer { return f(); }\n"
        "print(f());\nprint(g());\n"
    )
    root = act["tree"]
    assert root["label"] == "__main"
    assert [c["label"] for c in root["children"]] == ["f", "g"]
    assert [c["label"] for c in root["children"][1]["children"]] == ["f"]
    assert root["children"][0]["line"].startswith("$t") or "call f" in root["children"][0]["line"]


def test_recursion_is_marked_and_not_expanded():
    act = activation(
        "function fact(n: integer): integer { if (n <= 1) { return 1; } return n * fact(n - 1); }\n"
        "print(fact(4));\n"
    )
    fact = find(act["tree"], "fact")
    inner = find(fact, "fact")
    assert inner["recursive"] and inner["truncated"] and inner["children"] == []


def test_virtual_calls_use_the_static_type_and_are_marked():
    act = activation(
        "class A { function m(): integer { return 1; } }\n"
        "class B : A { function m(): integer { return 2; } }\n"
        "let x: A = new B();\nprint(x.m());\n"
    )
    node = find(act["tree"], "A.m")
    assert node is not None and node["virtual"] is True
