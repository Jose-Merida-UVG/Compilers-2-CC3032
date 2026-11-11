"""Closures: una función anidada que usa variables de la que la contiene.

Las variables capturadas (locales o parámetros de la función externa) pasan a
una casa fija del área global (`gp+N`); las que nadie anidado usa siguen en el
marco, así que una función recursiva con un ayudante anidado que no captura
nada conserva sus variables en la pila.
"""

from __future__ import annotations

from antlr4 import InputStream

from asm.generator import generate_asm
from asm.tac_parser import parse_tac
from compiler import analyze
from support.minisim import Sim

CLOSURE = """
function externa(n: integer): integer {
    let capturada: integer = 1;
    let propia: integer = 2;
    function interna(): integer {
        capturada = capturada + n;
        return capturada;
    }
    return interna() + propia;
}
print(externa(10));
"""


def _compile(src: str):
    r = analyze(InputStream(src))
    assert r["errors"] == [], r["errors"]
    return r


def _unit(program, label):
    return next(u for u in program.functions() if u.label == label)


def test_captured_variables_get_a_fixed_home_and_the_rest_stay_in_the_frame():
    r = _compile(CLOSURE)
    program = parse_tac(r["tac"], r["symbol_table_json"])
    externa, interna = _unit(program, "externa"), _unit(program, "interna")

    for unit in (externa, interna):  # la misma casa para quien declara y quien usa
        assert externa.symbols["capturada"]["address"] == unit.symbols["capturada"]["address"]
        assert unit.symbols["capturada"]["address"].startswith("gp+")
        assert unit.symbols["n"]["address"] == externa.symbols["n"]["address"]
        assert unit.symbols["n"]["static"] is True

    assert not externa.symbols["propia"].get("static")  # nadie anidado la usa
    assert externa.symbols["propia"]["address"].startswith("fp-")
    assert program.globals_size >= 8  # el área global creció para alojarlas


def test_a_captured_parameter_is_copied_from_the_stack_in_the_prologue():
    r = _compile(CLOSURE)
    text = "\n".join(generate_asm(r["tac"], r["symbol_table_json"]).lines)
    body = text[text.index("f_externa:"):text.index("f_externa__ret:")]
    assert "lw    $v1, 8($fp)" in body  # el parámetro `n` viene de la pila...
    assert "sw    $v1," in body and "($gp)" in body  # ...a su casa fija


def test_closure_program_runs():
    r = _compile(CLOSURE)
    assert Sim(generate_asm(r["tac"], r["symbol_table_json"]).lines).run() == "13\n"


def test_functions_without_closures_are_unchanged():
    r = _compile("function f(a: integer): integer { return a + 1; }\nprint(f(1));")
    program = parse_tac(r["tac"], r["symbol_table_json"])
    assert not any(s.get("static") for u in program.functions() for s in u.symbols.values())


def test_recursion_with_a_non_capturing_helper_keeps_its_variables_in_the_stack():
    src = """
function fact(n: integer): integer {
    let local: integer = n;
    function ayuda(x: integer): integer { return x + 1; }
    if (n <= 1) { return ayuda(0); }
    return local * fact(n - 1);
}
print(fact(5));
"""
    r = _compile(src)
    assert Sim(generate_asm(r["tac"], r["symbol_table_json"]).lines).run() == "120\n"
