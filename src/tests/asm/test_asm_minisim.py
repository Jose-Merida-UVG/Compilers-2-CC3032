"""Programas de punta a punta en el intérprete mínimo (sin MARS).

Cada carpeta de área (`aritmetica`, `logicas`, `arreglos`, `control_flujo`,
`funciones`, `recursividad`) tiene casos:

  valido_X.cps / valido_X.out   compila, se genera el `.s`, se ejecuta y su
                                salida debe ser EXACTAMENTE el `.out` (calculado
                                a mano, una línea por `print`).
  invalido_X.cps                debe dar errores y NO producir TAC ni ensamblador.

El intérprete (`support/minisim.py`) NO es MARS: es una red de seguridad rápida
para el desarrollo. Los mismos casos se corren además en MARS real
(`test_valid_programs_run_in_mars`), que se salta si no hay jar
(`MARS_JAR` o `src/tools/Mars4_5.jar`) o si falta `java`.
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
import tempfile

import pytest
from antlr4 import InputStream

from asm.generator import generate_asm
from compiler import analyze
from support.minisim import Sim

HERE = os.path.dirname(os.path.abspath(__file__))
AREAS = [
    "declaraciones",
    "aritmetica",
    "logicas",
    "arreglos",
    "control_flujo",
    "funciones",
    "recursividad",
    "clases",
    "herencia",
    "try_catch",
]


def _cases(pattern: str) -> list[str]:
    found: list[str] = []
    for area in AREAS:
        found += sorted(glob.glob(os.path.join(HERE, area, pattern)))
    return found


def _id(path: str) -> str:
    return os.path.relpath(path, HERE)


def compile_and_run(path: str) -> tuple[str, Sim]:
    with open(path, encoding="utf-8") as fh:
        result = analyze(InputStream(fh.read()))
    assert result["errors"] == [], f"{_id(path)}: {result['errors']}"
    asm = generate_asm(result["tac"], result["symbol_table_json"])
    sim = Sim(asm.lines)
    return sim.run(), sim


VALID = _cases("valido_*.cps")
INVALID = _cases("invalido_*.cps")


@pytest.mark.parametrize("path", VALID, ids=[_id(p) for p in VALID])
def test_valid_programs_print_the_expected_output(path):
    with open(path[:-4] + ".out", encoding="utf-8") as fh:
        expected = fh.read()
    out, sim = compile_and_run(path)
    assert out == expected
    assert sim.exit_code == 0


@pytest.mark.parametrize("path", INVALID, ids=[_id(p) for p in INVALID])
def test_invalid_programs_produce_no_tac_nor_assembly(path):
    with open(path, encoding="utf-8") as fh:
        result = analyze(InputStream(fh.read()))
    assert result["errors"] != [], f"{_id(path)} debería reportar errores"
    assert result["tac"] is None


# ── MARS real ───────────────────────────────────────────────────────────────
def _find_mars():
    candidates = [os.environ.get("MARS_JAR", ""), os.path.join(HERE, "..", "..", "tools", "Mars4_5.jar")]
    for c in candidates:
        if c and os.path.isfile(c):
            return os.path.abspath(c)
    return None


MARS = _find_mars()
needs_mars = pytest.mark.skipif(
    MARS is None or shutil.which("java") is None,
    reason="falta Mars4_5.jar (MARS_JAR o src/tools/) o java",
)


def run_in_mars(asm_lines: list[str], timeout: float = 60) -> subprocess.CompletedProcess:
    with tempfile.NamedTemporaryFile("w", suffix=".s", delete=False, encoding="utf-8") as fh:
        fh.write("\n".join(asm_lines) + "\n")
    try:
        return subprocess.run(
            ["java", "-Djava.awt.headless=true", "-jar", MARS, "nc", "sm", fh.name],
            capture_output=True, text=True, encoding="utf-8", timeout=timeout,
        )
    finally:
        os.unlink(fh.name)


@needs_mars
@pytest.mark.parametrize("path", VALID, ids=[_id(p) for p in VALID])
def test_valid_programs_run_in_mars(path):
    with open(path[:-4] + ".out", encoding="utf-8") as fh:
        expected = fh.read()
    with open(path, encoding="utf-8") as fh:
        result = analyze(InputStream(fh.read()))
    asm = generate_asm(result["tac"], result["symbol_table_json"])
    proc = run_in_mars(asm.lines)
    # MARS agrega un "\n" extra al terminar
    assert proc.stdout == expected + "\n", proc.stderr
    assert proc.returncode == 0
