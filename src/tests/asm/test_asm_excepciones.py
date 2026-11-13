"""Excepciones sin manejador: imprimen el mensaje y terminan con código 1."""

from __future__ import annotations

from antlr4 import InputStream

from asm.generator import generate_asm
from compiler import analyze
from support.minisim import Sim


def run(source: str) -> Sim:
    result = analyze(InputStream(source))
    assert result["errors"] == [], result["errors"]
    sim = Sim(generate_asm(result["tac"], result["symbol_table_json"]).lines)
    sim.output = sim.run()
    return sim


def test_index_out_of_range_without_try_terminates():
    sim = run("let a = [1];\nprint(1);\nprint(a[3]);\nprint(2);\n")
    assert sim.output == "1\nExcepcion no capturada: indice fuera de rango\n"
    assert sim.exit_code == 1


def test_null_field_access_without_try_terminates():
    sim = run(
        "class N { var v: integer; var s: N; function constructor() { this.s = null; } }\n"
        "let n = new N();\nprint(n.s.v);\n"
    )
    assert sim.output == "Excepcion no capturada: referencia nula\n"
    assert sim.exit_code == 1


def test_negative_index_is_catchable():
    sim = run(
        "let n: integer = 0 - 1;\n"
        "try {\n    let a: integer[] = [1];\n    print(a[n]);\n} catch (e) {\n    print(e);\n}\n"
    )
    assert sim.output == "indice fuera de rango\n"
    assert sim.exit_code == 0
