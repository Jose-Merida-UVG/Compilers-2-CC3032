"""Pruebas del helper TAC, reciclaje y bloqueo ante errores."""
from __future__ import annotations

import pytest

from conftest import compile_tac
from tac.generator import TACGenerator


def test_valid_source_generates_tac():
    errors, tac = compile_tac("let x = 2; print(x + 3);")

    assert errors == []
    assert tac == [
        "func __main():",
        "    x = 2",
        "    $t1 = x + 3",
        "    print $t1",
        "endfunc",
    ]


def test_shadowing_and_temporary_recycling():
    errors, tac = compile_tac(
        "let x = 1; { let x = 2; print(x + 3 + 4); } print(x);"
    )

    assert errors == []
    assert tac == [
        "func __main():",
        "    x = 1",
        "    x_1 = 2",
        "    $t1 = x_1 + 3",
        "    $t1 = $t1 + 4",
        "    print $t1",
        "    print x",
        "endfunc",
    ]


@pytest.mark.parametrize(
    "source",
    [
        pytest.param("let x = 1; @", id="lexical"),
        pytest.param("let x = ;", id="syntax"),
        pytest.param("print(no_declarada);", id="semantic"),
    ],
)
def test_errors_prevent_generator_execution(source, monkeypatch):
    def unexpected_visit(self, tree):
        pytest.fail("El generador no debe invocarse cuando hay errores")

    monkeypatch.setattr(TACGenerator, "visit", unexpected_visit)

    errors, tac = compile_tac(source)

    assert errors
    assert tac is None