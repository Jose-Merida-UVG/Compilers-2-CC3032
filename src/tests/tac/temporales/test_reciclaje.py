"""Reciclaje de temporales (R13): el pico de temporales de cada caso.

El generador siempre reutiliza el menor índice libre, así que el mayor `$tN`
usado en una función es la cantidad máxima de temporales vivos a la vez. Cada
caso fija ese pico: una cadena de sumas usa uno solo, una expresión con dos
subexpresiones independientes necesita más.
"""
import os
import re

import pytest

from conftest import compile_tac

_HERE = os.path.dirname(os.path.abspath(__file__))


def _peak(tac: list[str], unit: str) -> int:
    """Mayor índice `$tN` dentro de la unidad `unit`."""
    inside, highest = False, 0
    for line in tac:
        if line.startswith(f"func {unit}("):
            inside = True
        elif line == "endfunc":
            inside = False
        elif inside:
            highest = max([highest] + [int(n) for n in re.findall(r"\$t(\d+)", line)])
    return highest


def _tac(name: str) -> list[str]:
    with open(os.path.join(_HERE, name), encoding="utf-8") as f:
        errors, tac = compile_tac(f.read())
    assert errors == []
    return tac


@pytest.mark.parametrize(
    "case, unit, expected",
    [
        ("valido_expresiones_anidadas.cps", "__main", 3),
        ("valido_llamadas_anidadas.cps", "__main", 2),
        ("valido_reuso_entre_sentencias.cps", "__main", 2),
        ("valido_temporales_fijados.cps", "__main", 4),
    ],
)
def test_peak_temporaries(case, unit, expected):
    assert _peak(_tac(case), unit) == expected


def test_linear_chain_uses_a_single_temporary():
    errors, tac = compile_tac("let a = 1; let b = a + a + a + a + a + a + a;")
    assert errors == []
    assert _peak(tac, "__main") == 1


def test_temporaries_are_reused_across_statements():
    errors, tac = compile_tac("let a = 1; let x = a * 2; let y = a * 3; let z = a * 4;")
    assert errors == []
    # Cada sentencia termina con su temporal liberado: siempre se pide $t1
    assert [line.strip() for line in tac if "*" in line] == ["$t1 = a * 2", "$t1 = a * 3", "$t1 = a * 4"]


def test_each_function_has_its_own_pool():
    errors, tac = compile_tac(
        "function f(a: integer, b: integer): integer { return (a + b) * (a - b); }"
        "function g(x: integer): integer { return x + 1; }"
        "print(f(1, 2) + g(3));"
    )
    assert errors == []
    assert _peak(tac, "f") == 2
    assert _peak(tac, "g") == 1  # el pool de f no se arrastra a g
