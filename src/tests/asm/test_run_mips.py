"""`src/run_mips.py` y el endpoint `/api/exec`: compilar un .cps y ejecutarlo en MARS."""

from __future__ import annotations

import os

import run_mips
from run_mips import execute, main
from server import RunBody, exec_file
from test_asm_minisim import needs_mars

DEMOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "workspace", "input", "comp-mips")
LOOP = [".text", ".globl main", "main:", "    j     main"]


@needs_mars
def test_cli_runs_a_program_and_prints_its_output(capfd):
    assert main([os.path.join(DEMOS, "15-activacion-valido.cps")]) == 0
    assert capfd.readouterr().out == "80\n42\n13\n"


def test_cli_reports_errors_and_runs_nothing(capfd):
    assert main([os.path.join(DEMOS, "15-activacion-invalido.cps")]) == 1
    assert "se esperaban 1 argumento" in capfd.readouterr().out


@needs_mars
def test_execute_kills_a_program_that_never_ends():
    run = execute(LOOP, timeout=1)
    assert run["available"] and run["timedOut"] and run["exitCode"] is None


def test_execute_says_so_when_mars_is_missing(monkeypatch):
    monkeypatch.setattr(run_mips, "find_mars", lambda: None)
    run = execute(LOOP)
    assert run["available"] is False and run["output"] == ""


@needs_mars
def test_endpoint_runs_a_valid_demo():
    reply = exec_file(RunBody(inputPath="input/comp-mips/15-activacion-valido.cps"))
    assert reply["ran"] and reply["errors"] == []
    assert reply["output"] == "80\n42\n13\n" and reply["exitCode"] == 0


def test_endpoint_returns_errors_and_does_not_run_an_invalid_demo():
    reply = exec_file(RunBody(inputPath="input/comp-mips/15-activacion-invalido.cps"))
    assert reply["ran"] is False and reply["errors"] and reply["output"] == ""


def test_run_saves_only_the_generated_code(tmp_path, monkeypatch):
    import server

    (tmp_path / "input").mkdir()
    (tmp_path / "input" / "p.cps").write_text("let x: integer = 2;\nprint(x * 3);\n", encoding="utf-8")
    monkeypatch.setattr(server, "WORKSPACE", tmp_path)
    reply = server.run_file(RunBody(inputPath="input/p.cps"))
    assert reply["errors"] == [] and reply["tac"] and reply["asm"]
    assert sorted(f.name for f in (tmp_path / "output" / "p").iterdir()) == ["p.cps.s", "p.cps.tac"]
