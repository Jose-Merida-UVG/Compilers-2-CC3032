"""Programas de estrés por área de la rúbrica: se compilan, se ejecutan y se compara la salida."""

from __future__ import annotations

import pytest
from antlr4 import InputStream

from asm.generator import generate_asm
from asm.peephole import optimize
from compiler import analyze
from support.minisim import Sim
from tests.asm.estres_casos import C

# Limitaciones conocidas del lenguaje o del generador.
CONOCIDOS = {
    "mutua": "el lenguaje no permite usar una función antes de declararla",
    "division_por_cero_observar": "MARS no lanza excepción; el resultado no está definido",
    "arreglo_mixto_de_subclases": "el checker del P1 exige elementos del mismo tipo exacto",
    "closure_con_recursion_del_contenedor_conocido": "la variable capturada vive en una casa fija de $gp",
}


@pytest.mark.parametrize("area,name,src,expected", C, ids=[f"{a}/{n}" for a, n, _, _ in C])
def test_programa(area, name, src, expected):
    if name in CONOCIDOS:
        pytest.skip(CONOCIDOS[name])
    result = analyze(InputStream(src))
    assert result["errors"] == [], result["errors"]
    raw = generate_asm(result["tac"], result["symbol_table_json"]).lines
    for lines in (raw, optimize(raw)[0]):
        out = Sim(lines).run()
        if isinstance(expected, tuple):
            assert expected[1] in out
        else:
            assert out == expected
