"""Los demos del IDE (`workspace/input/comp-mips/`): cada válido compila a MIPS y corre.

Los inválidos deben dar errores y no producir ensamblador. Los válidos se ejecutan
en el intérprete mínimo y, si hay MARS, la salida de ambos debe coincidir. Los
demos del P3 (`14-registros`, `15-activacion`) además tienen su salida calculada a mano.
"""

from __future__ import annotations

import glob
import os

import pytest
from antlr4 import FileStream

from asm.generator import generate_asm
from compiler import analyze
from support.minisim import Sim
from test_asm_minisim import needs_mars, run_in_mars

DEMOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "workspace", "input", "comp-mips")
VALID = sorted(glob.glob(os.path.join(DEMOS, "*-valido.cps")) + glob.glob(os.path.join(DEMOS, "13-*.cps")))
INVALID = sorted(glob.glob(os.path.join(DEMOS, "*-invalido.cps")))

# salida calculada a mano (suma 1..13 = 91; 3*7*11 - 15*19 = -54; 1.5*2.5 + 4 = 7.75)
EXPECTED = {
    "14-registros-valido.cps": "91\n-54\n7.75\n",
    # 3² + 4² + fib(10) = 9 + 16 + 55; 21*2; fib(7)
    "15-activacion-valido.cps": "80\n42\n13\n",
}


def compile_demo(path: str) -> dict:
    return analyze(FileStream(path, encoding="utf-8"))


def _id(path: str) -> str:
    return os.path.basename(path)


def test_demos_were_found():
    assert len(VALID) >= 13 and len(INVALID) >= 12


@pytest.mark.parametrize("path", VALID, ids=[_id(p) for p in VALID])
def test_valid_demo_compiles_to_mips_and_runs(path):
    result = compile_demo(path)
    assert result["errors"] == []
    assert result["asm"] and result["activation"]["frames"]
    sim = Sim(result["asm"])
    out = sim.run()
    assert sim.exit_code == 0
    if _id(path) in EXPECTED:
        assert out == EXPECTED[_id(path)]


@pytest.mark.parametrize("path", INVALID, ids=[_id(p) for p in INVALID])
def test_invalid_demo_reports_errors_and_no_assembly(path):
    result = compile_demo(path)
    assert result["errors"]
    assert result["tac"] is None and result["asm"] is None


@needs_mars
@pytest.mark.parametrize("path", VALID, ids=[_id(p) for p in VALID])
def test_valid_demo_prints_the_same_in_mars(path):
    result = compile_demo(path)
    sim_out = Sim(result["asm"]).run()
    proc = run_in_mars(generate_asm(result["tac"], result["symbol_table_json"]).lines)
    assert proc.stdout == sim_out + "\n", proc.stderr  # MARS agrega un "\n" al terminar
    assert proc.returncode == 0
