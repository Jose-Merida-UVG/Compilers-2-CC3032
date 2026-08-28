"""Fase 0 smoke tests.

These aren't semantic-rule tests (those live under src/tests/semantic/
<categoria>/, one battery per rule, owned per docs/plan-proyecto1.md) --
this file just guards the Fase 0 wiring itself:
  1. Every pre-existing sample under workspace/input/ still analyzes
     exactly as before now that SemanticChecker is wired into
     compiler.analyze() (it's a no-op today, so lexical/syntax results
     must be unaffected).
  2. The new `float` type/literal (grammar change) actually parses.

(A third smoke test, `test_semantic_checker_is_still_a_noop`, guarded that
the checker produced zero errors while every rule method was still an
unimplemented `visitChildren` passthrough. It started failing -- as its own
docstring said it eventually would -- once visitIdentifierExpr began
reporting undeclared variables, so it was removed here. Real coverage for
ámbito rules like that one now belongs in
src/tests/semantic/ambito/valido_*.cps / invalido_*.cps instead.)
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