"""Semantic error collection.

Mirrors the pattern in `error_listener.py` (Spanish messages, line/column,
one flat list) but for errors raised while *walking the already-built
parse tree*, as opposed to lexical/syntax errors raised by ANTLR itself
during lexing/parsing. Kept as a separate list on purpose -- `compiler.py`
only runs the semantic pass when the lexical/syntax list is empty, so the
two never need to be merged mid-analysis, only concatenated for display.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SemanticError:
    line: int
    column: int
    message: str

    def __str__(self) -> str:
        return f"Error semántico en línea {self.line}, columna {self.column}: {self.message}."


class SemanticErrorList:
    def __init__(self) -> None:
        self.errors: list[SemanticError] = []

    def add(self, line: int, column: int, message: str) -> None:
        self.errors.append(SemanticError(line, column, message))

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def as_strings(self) -> list[str]:
        return [str(e) for e in self.errors]
