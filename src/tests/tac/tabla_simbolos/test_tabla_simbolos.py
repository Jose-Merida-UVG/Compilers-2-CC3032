"""Tabla de símbolos con datos para código objeto (R12): tamaños, offsets,
direcciones, etiquetas, registros de activación y layout de clases.

- Golden: cada `valido_X.cps` de esta carpeta tiene un `valido_X.symbols.json`
  con el JSON de `Scope.to_dict()` tras `assign_layout` (lo que recibe la
  GUI). `UPDATE_GOLDEN=1` lo regenera; revisar el diff a mano.
- Reglas: pruebas explícitas de las convenciones de semantic/layout.py.
"""
import glob
import json
import os
from typing import Optional

import pytest
from antlr4 import CommonTokenStream, InputStream

from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from semantic.checker import SemanticChecker
from semantic.layout import assign_layout
from semantic.symbols import Scope, ScopeKind
from tac.generator import TACGenerator

_HERE = os.path.dirname(os.path.abspath(__file__))
_VALID = sorted(glob.glob(os.path.join(_HERE, "valido_*.cps")))


def _layout(source: str) -> Scope:
    """Mismo recorrido que la integración: checker, TAC (para max_temps) y
    luego assign_layout."""
    parser = CompiscriptParser(CommonTokenStream(CompiscriptLexer(InputStream(source))))
    tree = parser.program()
    checker = SemanticChecker()
    assert checker.check(tree).as_strings() == []
    generator = TACGenerator(checker)
    generator.visit(tree)
    assign_layout(checker.symbols.global_scope, generator.e.max_temps, generator.name_of)
    return checker.symbols.global_scope


def _find(scope: Scope, kind: ScopeKind, owner: str) -> Optional[Scope]:
    if scope.kind is kind and scope.owner == owner:
        return scope
    for child in scope.children:
        found = _find(child, kind, owner)
        if found is not None:
            return found
    return None


def _symbol(scope: Scope, name: str):
    """Símbolo `name` en `scope` o en los bloques anidados."""
    if name in scope.symbols:
        return scope.symbols[name]
    for child in scope.children:
        if child.kind is ScopeKind.BLOCK:
            found = _symbol(child, name)
            if found is not None:
                return found
    return None


@pytest.mark.parametrize("path", _VALID, ids=os.path.basename)
def test_symbol_table_matches_golden(path):
    with open(path, encoding="utf-8") as f:
        actual = json.dumps(_layout(f.read()).to_dict(), indent=2, ensure_ascii=False) + "\n"

    golden = os.path.splitext(path)[0] + ".symbols.json"
    if os.environ.get("UPDATE_GOLDEN"):
        with open(golden, "w", encoding="utf-8") as f:
            f.write(actual)
    assert os.path.exists(golden), f"falta {os.path.basename(golden)}; genéralo con UPDATE_GOLDEN=1"
    with open(golden, encoding="utf-8") as f:
        assert actual == f.read()


def test_globals_sizes_alignment_and_addresses():
    g = _layout("let a: integer = 1; let ok: boolean = true; let f: float = 2.5; let s = \"x\";")
    sym = g.symbols
    assert [(s.size, s.offset, s.address) for s in sym.values()] == [
        (4, 0, "gp+0"),
        (1, 4, "gp+4"),
        (4, 8, "gp+8"),  # el float se alinea a 4 tras el boolean
        (4, 12, "gp+12"),  # string = referencia de 4
    ]


def test_function_frame_params_locals_and_temps():
    g = _layout(
        "function f(a: integer, b: boolean, c: float): integer {"
        "  let x: integer = a; let ok: boolean = b; { let y: integer = a * 2 + x * 3; }"
        "  return x; }"
        "print(f(1, true, 2.0));"
    )
    scope = _find(g, ScopeKind.FUNCTION, "f")
    assert [(s.offset, s.address) for s in scope.symbols.values()] == [
        (0, "fp+8"),   # a: primer parámetro, justo sobre ra y fp guardados
        (4, "fp+12"),  # b (boolean, 1 byte)
        (8, "fp+16"),  # c se alinea a 4
    ]
    assert _symbol(scope, "x").address == "fp-4"
    assert _symbol(scope, "ok").address == "fp-5"
    assert _symbol(scope, "y").address == "fp-12"  # int alineado tras el boolean
    frame = scope.frame
    assert frame["label"] == "f"
    assert frame["params_size"] == 12
    assert frame["locals_size"] == 12
    assert frame["saved_size"] == 8
    assert frame["temps"] == 2  # `a * 2 + x * 3` tiene vivos dos temporales a la vez
    assert frame["temps_size"] == 8
    assert frame["total_size"] == 12 + 12 + 8 + 8


def test_method_has_this_slot_and_class_label():
    g = _layout(
        "class C { var v: integer = 0; function m(k: integer): integer { return this.v + k; } }"
        "let c = new C(); print(c.m(1));"
    )
    method = _find(g, ScopeKind.FUNCTION, "m")
    assert method.symbols["k"].address == "fp+12"  # offset 0 es `this`
    assert method.frame["label"] == "C.m"
    assert method.frame["params_size"] == 8
    assert _find(g, ScopeKind.CLASS, "C").symbols["m"].label == "C.m"


def test_class_layout_inherited_fields_keep_parent_offsets():
    g = _layout(
        "class A { var x: integer = 1; var ok: boolean = true; function f(): integer { return 1; } }"
        "class B : A { var y: integer = 2; function f(): integer { return 2; } }"
        "class C : B { var z: float = 1.0; }"
        "let c = new C(); print(c.f());"
    )
    a = _find(g, ScopeKind.CLASS, "A").layout
    b = _find(g, ScopeKind.CLASS, "B").layout
    c = _find(g, ScopeKind.CLASS, "C").layout

    assert a["size"] == 8 and a["parent"] is None
    assert [(f["name"], f["offset"], f["inherited"]) for f in a["fields"]] == [
        ("x", 0, False),
        ("ok", 4, False),
    ]
    # B conserva x y ok donde estaban y agrega y después del tamaño de A
    assert [(f["name"], f["offset"], f["inherited"]) for f in b["fields"]] == [
        ("x", 0, True),
        ("ok", 4, True),
        ("y", 8, False),
    ]
    assert b["size"] == 12 and b["parent"] == "A"
    assert [(f["name"], f["offset"]) for f in c["fields"]] == [("x", 0), ("ok", 4), ("y", 8), ("z", 12)]
    assert c["size"] == 16 and c["parent"] == "B"

    assert a["methods"] == [{"name": "f", "label": "A.f", "overrides": None}]
    assert b["methods"] == [{"name": "f", "label": "B.f", "overrides": "A.f"}]
    assert c["methods"] == []
    assert g.symbols["C"].size == 16  # el símbolo de la clase guarda su tamaño


def test_constructor_is_not_reported_as_override():
    g = _layout(
        "class A { var x: integer; function constructor(a: integer) { this.x = a; } }"
        "class B : A { function constructor(a: integer) { this.x = a + 1; } }"
        "let b = new B(1);"
    )
    methods = _find(g, ScopeKind.CLASS, "B").layout["methods"]
    assert methods == [{"name": "constructor", "label": "B.constructor", "overrides": None}]


def test_to_dict_exposes_new_fields_only_where_they_apply():
    data = _layout("function f(a: integer) { print(a); } class C { var v: integer = 0; } f(1);").to_dict()
    symbol = data["symbols"][0]
    assert set(symbol) >= {"size", "offset", "address", "label", "tac_name"}
    # El ámbito global solo trae el frame de __main, nunca un layout de clase
    assert data["frame"]["label"] == "__main" and "layout" not in data
    kinds = {child["kind"]: child for child in data["children"]}
    assert "frame" in kinds["FUNCTION"] and "layout" not in kinds["FUNCTION"]
    assert "layout" in kinds["CLASS"] and "frame" not in kinds["CLASS"]


def test_main_has_its_own_frame_with_the_real_temp_peak():
    g = _layout("let a: integer = 1; let b: integer = 2; print((a + b) * (a - b));")
    # Las variables de nivel superior son globales (gp), no ocupan el frame
    assert g.frame == {
        "label": "__main",
        "params_size": 0,
        "locals_size": 0,
        "temps": 2,
        "temps_size": 8,
        "saved_size": 8,
        "total_size": 16,
    }
    assert g.symbols["a"].address == "gp+0"


def test_tac_name_follows_the_names_used_in_the_tac():
    g = _layout("let x: integer = 1; { let x: integer = 2; print(x); } print(x);")
    outer = g.symbols["x"]
    inner = g.children[0].symbols["x"]
    assert (outer.tac_name, inner.tac_name) == ("x", "x_1")
    assert (outer.address, inner.address) == ("gp+0", "gp+4")
