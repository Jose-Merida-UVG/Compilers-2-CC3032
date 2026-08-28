"""Fase 0 smoke tests.

These aren't semantic-rule tests (those live under src/tests/semantic/
<categoria>/, one battery per rule, owned per docs/plan-proyecto1.md) --
this file just guards the Fase 0 wiring itself:
  1. Every pre-existing sample under workspace/input/ still analyzes
     exactly as before now that SemanticChecker is wired into
     compiler.analyze() (it's a no-op today, so lexical/syntax results
     must be unaffected).
  2. The new `float` type/literal (grammar change) actually parses.
"""
import glob
import os

import pytest

from compiler import analyze_file

_HERE = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE_INPUT = os.path.join(_HERE, "..", "..", "workspace", "input")
_SAMPLES = sorted(glob.glob(os.path.join(_WORKSPACE_INPUT, "**", "*.cps"), recursive=True))


@pytest.mark.parametrize("path", _SAMPLES, ids=[os.path.basename(p) for p in _SAMPLES])
def test_existing_samples_still_analyze(path):
    result = analyze_file(path)
    assert "errors" in result
    assert "status_message" in result
    assert "tree_json" in result


def test_float_type_and_literal_parse(tmp_path):
    src = tmp_path / "float_smoke.cps"
    src.write_text(
        "let pi: float = 3.14;\n"
        "let r: integer = 2;\n"
        "let area: float = pi * r * r;\n"
        "print(area);\n"
    )
    result = analyze_file(str(src))
    assert result["errors"] == []


def test_semantic_checker_is_still_a_noop():
    """Sanity check for Fase 0: until each rule method in
    semantic/checker.py is filled in, valid syntax should never produce a
    semantic error. This test should start failing (in a good way) as
    people implement their rules -- update/remove it then."""
    from semantic.checker import SemanticChecker

    # Deliberately semantically wrong (undeclared var, type mismatch) but
    # syntactically valid -- once ambito/tipos rules exist, this should
    # start reporting errors; for now (no-op checker) it must not.
    import CompiscriptLexer
    import CompiscriptParser
    from antlr4 import CommonTokenStream, InputStream

    lexer = CompiscriptLexer.CompiscriptLexer(InputStream("let x: integer = \"oops\";\nprint(y);\n"))
    parser = CompiscriptParser.CompiscriptParser(CommonTokenStream(lexer))
    tree = parser.program()

    result = SemanticChecker().check(tree)
    assert result.as_strings() == []
