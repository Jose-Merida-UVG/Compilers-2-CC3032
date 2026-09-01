"""Batería 'Control de Flujo' (Persona 3): condiciones boolean en
if/while/do-while/for/switch, break/continue solo en bucles, return solo
dentro de una función. Ver ../README.md para la convención de nombres.
"""
import glob
import os

import pytest

from compiler import analyze_file

_HERE = os.path.dirname(os.path.abspath(__file__))
_VALID = sorted(glob.glob(os.path.join(_HERE, "valido_*.cps")))
_INVALID = sorted(glob.glob(os.path.join(_HERE, "invalido_*.cps")))


@pytest.mark.parametrize("path", _VALID, ids=[os.path.basename(p) for p in _VALID])
def test_valid_cases_have_no_errors(path):
    result = analyze_file(path)
    assert result["errors"] == [], f"{os.path.basename(path)}: {result['errors']}"


@pytest.mark.parametrize("path", _INVALID, ids=[os.path.basename(p) for p in _INVALID])
def test_invalid_cases_report_an_error(path):
    result = analyze_file(path)
    assert result["errors"] != [], f"{os.path.basename(path)} should have reported an error"
