"""`src/run_mips.py`: compila un .cps y lo ejecuta en MARS."""

from __future__ import annotations

import os

from run_mips import main
from test_asm_minisim import needs_mars

DEMOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "workspace", "input", "comp-mips")


@needs_mars
def test_runs_a_program_and_prints_its_output(capfd):
    assert main([os.path.join(DEMOS, "15-activacion-valido.cps")]) == 0
    assert capfd.readouterr().out == "80\n42\n13\n"


def test_errors_are_reported_and_nothing_runs(capfd):
    assert main([os.path.join(DEMOS, "15-activacion-invalido.cps")]) == 1
    assert "se esperaban 1 argumento" in capfd.readouterr().out
