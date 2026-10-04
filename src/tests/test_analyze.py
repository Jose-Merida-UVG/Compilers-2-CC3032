"""`compiler.analyze` de punta a punta: recuperación de errores (R6), errores
sin repetir (R7), TAC solo sin errores (R8) y los datos que recibe la GUI
(TAC, estadísticas y tabla de símbolos con layout).
"""
import re

import pytest
from antlr4 import InputStream

import compiler
from compiler import analyze


def run(source: str) -> dict:
    return analyze(InputStream(source))


LEXICAL = "let a@ = 1;\nlet b: integer = 2;\nlet c# = 3;\nlet d: integer = 4 ~ 1;\n"
SYNTAX = "let a: integer = 1\nlet b: integer = 2\nlet c: integer = 3\nprint(a);\n"
SEMANTIC = 'let x: integer = "a";\nprint(y);\n'
VALID = "function f(a: integer): integer { return a + 1; }\nprint(f(1));\n"


def test_lexical_errors_are_all_reported_not_just_the_first():
    errors = run(LEXICAL)["errors"]
    assert all("léxico" in e for e in errors)
    assert [int(re.search(r"línea (\d+)", e).group(1)) for e in errors] == [1, 3, 4]


@pytest.mark.parametrize(
    "source",
    ["let a@ integer = 1;", "let d: integer = 4 ~ 1;", "let b = 1 #", "@let x = 1;"],
)
def test_lexical_error_does_not_cascade_into_a_syntax_error(source):
    """El texto que descarta el lexer deja un hueco; el error sintáctico que
    eso provoca es un mensaje derivado (R7) y no se reporta."""
    errors = run(source)["errors"]
    assert len(errors) == 1 and "léxico" in errors[0]


def test_independent_syntax_errors_are_kept_next_to_lexical_ones():
    errors = run("let a@ = 1;\nlet b: integer = 2\nlet c: integer = 3;\n")["errors"]
    assert [e.split(":")[0] for e in errors] == [
        "Error léxico en línea 1, columna 5",
        "Error sintáctico en línea 3, columna 0",
    ]
    # Misma línea, pero el token inesperado no sigue al texto descartado
    errors = run("let a@ = 1; let b = 2 let c = 3;")["errors"]
    assert [("léxico" in e, "sintáctico" in e) for e in errors] == [(True, False), (False, True)]


def test_syntax_errors_are_all_reported_not_just_the_first():
    result = run(SYNTAX)
    lines = [int(re.search(r"línea (\d+)", e).group(1)) for e in result["errors"]]
    assert lines == [2, 3, 4]


@pytest.mark.parametrize("source", [LEXICAL, SYNTAX, SEMANTIC])
def test_no_repeated_errors(source):
    errors = run(source)["errors"]
    assert len(errors) == len(set(errors))


@pytest.mark.parametrize("source", [LEXICAL, SYNTAX, SEMANTIC])
def test_any_error_means_no_tac(source):
    result = run(source)
    assert result["errors"]
    assert result["tac"] is None
    assert result["tac_stats"] is None
    assert "No se generó código intermedio" in result["status_message"]


def test_lexical_and_syntax_errors_skip_semantic_analysis():
    assert run(LEXICAL)["symbol_table_json"] is None
    assert run(SYNTAX)["symbol_table_json"] is None


def test_semantic_errors_still_return_the_symbol_table():
    result = run(SEMANTIC)
    assert result["symbol_table_json"] is not None
    assert all("semántico" in e for e in result["errors"])


def test_valid_program_returns_tac_and_stats():
    result = run(VALID)
    assert result["errors"] == []
    assert result["tac"] == [
        "func f(a):",
        "    $t1 = a + 1",
        "    return $t1",
        "endfunc",
        "func __main():",
        "    param 1",
        "    $t1 = call f, 1",
        "    print $t1",
        "endfunc",
    ]
    # instrucciones: todo salvo func/endfunc; temps: pico de una función
    assert result["tac_stats"] == {"instructions": 5, "temps": 1, "functions": 2}
    assert "Código intermedio generado (5 instrucciones)" in result["status_message"]


def test_symbol_table_carries_layout_data():
    table = run("let g: integer = 1; let ok: boolean = true; " + VALID)["symbol_table_json"]
    by_name = {s["name"]: s for s in table["symbols"]}
    assert by_name["g"]["address"] == "gp+0"
    assert by_name["ok"]["address"] == "gp+4"
    assert by_name["f"]["label"] == "f"

    function_scope = next(c for c in table["children"] if c["kind"] == "FUNCTION")
    frame = function_scope["frame"]
    assert frame["label"] == "f"
    assert frame["temps"] == 1  # viene del pico de temporales del TAC
    assert frame["total_size"] == 4 + 0 + 4 + 8


def test_generator_failure_is_reported_not_raised(monkeypatch):
    def boom(self, tree):
        raise RuntimeError("fallo simulado")

    monkeypatch.setattr(compiler.TACGenerator, "visit", boom)
    result = run(VALID)
    assert result["tac"] is None
    assert result["tac_stats"] is None
    assert any("Error interno al generar el código intermedio" in e for e in result["errors"])
