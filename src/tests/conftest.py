"""Makes `import compiler`, `from semantic...`, etc. work from any test
file under src/tests/, regardless of how pytest is invoked (IDE, `make
test`, bare `pytest`) -- mirrors the PYTHONPATH=src/generated:src that the
Makefile/README already use for the CLI and server.
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.dirname(_HERE)
_GENERATED = os.path.join(_SRC, "generated")

for path in (_GENERATED, _SRC):
    if path not in sys.path:
        sys.path.insert(0, path)

from antlr4 import CommonTokenStream, InputStream

from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from error_listener import CompiscriptErrorListener
from semantic.checker import SemanticChecker
from tac.generator import TACGenerator

def compile_tac(source: str) -> tuple[list[str], list[str] | None]:
    """Analiza el fuente y genera TAC únicamente si no hay errores."""
    listener = CompiscriptErrorListener()

    lexer = CompiscriptLexer(InputStream(source))
    lexer.removeErrorListeners()
    lexer.addErrorListener(listener)

    parser = CompiscriptParser(CommonTokenStream(lexer))
    parser.removeErrorListeners()
    parser.addErrorListener(listener)

    tree = parser.program()
    errors = list(listener.errors)
    if errors:
        return errors, None

    checker = SemanticChecker()
    errors = checker.check(tree).as_strings()
    if errors:
        return errors, None

    generator = TACGenerator(checker)
    tac = generator.visit(tree)

    assert generator.e.live_temps() == 0, "Quedaron temporales vivos"
    return [], tac
