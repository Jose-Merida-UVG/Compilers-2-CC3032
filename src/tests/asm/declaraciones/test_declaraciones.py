"""Declaraciones en el simulador local; la validación en MARS es aparte."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from compiler import analyze_file

# Permite ejecutar esta carpeta sola, sin depender del orden de colección.
HERE = Path(__file__).resolve().parent
ASM_TESTS = str(HERE.parent)
if ASM_TESTS not in sys.path:
    sys.path.insert(0, ASM_TESTS)
from support.minisim import Sim


@pytest.mark.parametrize("path", sorted(HERE.glob("valido_*.cps")), ids=lambda p: p.stem)
def test_valid_declarations(path):
    result = analyze_file(str(path))
    assert result["errors"] == []
    assert result["tac"] is not None
    assert result["asm"] is not None
    expected = path.with_suffix(".out").read_text(encoding="utf-8")
    sim = Sim(result["asm"])
    assert sim.run() == expected
    assert sim.exit_code == 0


@pytest.mark.parametrize("path", sorted(HERE.glob("invalido_*.cps")), ids=lambda p: p.stem)
def test_invalid_declarations_block_codegen(path, monkeypatch):
    def unexpected_codegen(*args, **kwargs):
        pytest.fail("No debe generarse ensamblador para un fuente inválido")

    monkeypatch.setattr("compiler.generate_asm", unexpected_codegen)
    result = analyze_file(str(path))
    assert result["errors"]
    for key in ("tac", "tac_stats", "asm", "asm_raw", "asm_stats", "activation"):
        assert result[key] is None, key
