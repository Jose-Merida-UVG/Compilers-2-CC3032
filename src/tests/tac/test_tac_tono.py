"""Batería de TAC de Tono: funciones, recursividad, clases, herencia y
tabla de símbolos (contrato §8).

A diferencia de `test_tac_golden.py` (que se salta hasta que `analyze()`
devuelva el TAC), aquí se usa `compile_tac` directo, así que estos casos
se ejecutan siempre.

- `valido_X.cps`  -> sin errores y TAC idéntico a `valido_X.tac` (golden).
  `compile_tac` además falla si queda un temporal vivo (fuga) y el
  Emitter lo comprueba al cerrar cada función.
- `invalido_X.cps` -> al menos un error y ningún TAC (R8).

Regenerar golden: `UPDATE_GOLDEN=1 make test ARGS="src/tests/tac/test_tac_tono.py"`
y revisar el diff a mano.
"""
import glob
import os

import pytest

from conftest import compile_tac

_HERE = os.path.dirname(os.path.abspath(__file__))
_AREAS = ("funciones", "recursividad", "clases", "herencia", "tabla_simbolos")


def _cases(prefix: str) -> list[str]:
    return sorted(
        path
        for area in _AREAS
        for path in glob.glob(os.path.join(_HERE, area, f"{prefix}_*.cps"))
    )


def _id(path: str) -> str:
    return os.path.relpath(path, _HERE)


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


@pytest.mark.parametrize("path", _cases("valido"), ids=_id)
def test_valid_case_matches_golden(path):
    errors, tac = compile_tac(_read(path))
    assert errors == [], f"{_id(path)}: {errors}"
    assert tac, f"{_id(path)}: no se generó TAC"
    actual = "\n".join(tac) + "\n"

    golden = os.path.splitext(path)[0] + ".tac"
    if os.environ.get("UPDATE_GOLDEN"):
        with open(golden, "w", encoding="utf-8") as f:
            f.write(actual)
    assert os.path.exists(golden), f"falta {_id(golden)}; genéralo con UPDATE_GOLDEN=1"
    assert actual == _read(golden)


@pytest.mark.parametrize("path", _cases("invalido"), ids=_id)
def test_invalid_case_reports_errors_and_no_tac(path):
    errors, tac = compile_tac(_read(path))
    assert errors != [], f"{_id(path)} debería reportar un error"
    assert tac is None, f"{_id(path)}: con errores no debe haber TAC"


def test_every_area_has_enough_cases():
    """≥3 válidos y ≥2 inválidos por área (contrato 02-tono.md)."""
    for area in _AREAS:
        valid = glob.glob(os.path.join(_HERE, area, "valido_*.cps"))
        invalid = glob.glob(os.path.join(_HERE, area, "invalido_*.cps"))
        assert len(valid) >= 3, f"{area}: solo {len(valid)} válidos"
        assert len(invalid) >= 2, f"{area}: solo {len(invalid)} inválidos"
