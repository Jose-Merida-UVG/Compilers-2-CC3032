"""Batería de TAC: una carpeta por área (declaraciones, aritmetica,
logicas, arreglos, control_flujo, ...) con casos `valido_*.cps` y
`invalido_*.cps`.

- `valido_X.cps`   -> sin errores y con TAC generado.
- `invalido_X.cps` -> al menos un error y **no se genera TAC** (R8).

Qué hace el TAC de cada caso se comprueba en `test_tac_invariantes.py`
(estructura) y `test_cobertura_rubrica.py` (instrucciones esperadas).
"""
import glob
import os

import pytest

from compiler import analyze_file

_HERE = os.path.dirname(os.path.abspath(__file__))
_VALID = sorted(glob.glob(os.path.join(_HERE, "*", "valido_*.cps")))
_INVALID = sorted(glob.glob(os.path.join(_HERE, "*", "invalido_*.cps")))


def _id(path: str) -> str:
    return os.path.relpath(path, _HERE)


@pytest.mark.parametrize("path", _VALID, ids=[_id(p) for p in _VALID])
def test_valid_cases_generate_tac(path):
    result = analyze_file(path)
    assert result["errors"] == [], f"{_id(path)}: {result['errors']}"
    assert result["tac"], f"{_id(path)}: no se generó TAC"


@pytest.mark.parametrize("path", _INVALID, ids=[_id(p) for p in _INVALID])
def test_invalid_cases_report_errors_and_no_tac(path):
    result = analyze_file(path)
    assert result["errors"] != [], f"{_id(path)} debería reportar un error"
    assert result["tac"] is None, f"{_id(path)}: con errores no debe haber TAC"
