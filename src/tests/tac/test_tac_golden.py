"""Batería de TAC: una carpeta por área (declaraciones, aritmetica,
logicas, arreglos, control_flujo, ...) con casos `valido_*.cps` y
`invalido_*.cps`. Ver docs/proyecto2/00-contrato.md §8.

- `valido_X.cps`  -> sin errores, y su TAC es idéntico a `valido_X.tac`
  (archivo "golden", texto exacto).
- `invalido_X.cps` -> al menos un error y **no se genera TAC** (R8).

Regenerar los golden tras un cambio intencional:
    UPDATE_GOLDEN=1 make test ARGS="src/tests/tac"
y revisar el diff a mano antes de aceptarlo.

Se saltan los casos mientras `analyze` no devuelva la clave "tac"
(integración de compiler.py pendiente).
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
def test_valid_cases_match_golden_tac(path):
    result = analyze_file(path)
    assert result["errors"] == [], f"{_id(path)}: {result['errors']}"
    if "tac" not in result:
        pytest.skip("analyze() aún no genera TAC")
    assert result["tac"], f"{_id(path)}: no se generó TAC"
    actual = "\n".join(result["tac"]) + "\n"

    golden_path = os.path.splitext(path)[0] + ".tac"
    if os.environ.get("UPDATE_GOLDEN"):
        with open(golden_path, "w", encoding="utf-8") as f:
            f.write(actual)
    assert os.path.exists(golden_path), (
        f"falta {_id(golden_path)}; genéralo con UPDATE_GOLDEN=1 y revísalo"
    )
    with open(golden_path, encoding="utf-8") as f:
        assert actual == f.read()


@pytest.mark.parametrize("path", _INVALID, ids=[_id(p) for p in _INVALID])
def test_invalid_cases_report_errors_and_no_tac(path):
    result = analyze_file(path)
    assert result["errors"] != [], f"{_id(path)} debería reportar un error"
    if "tac" in result:
        assert result["tac"] is None, f"{_id(path)}: con errores no debe haber TAC"
