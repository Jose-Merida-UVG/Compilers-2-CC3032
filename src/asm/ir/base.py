"""Clase base de las instrucciones del IR y utilidades comunes."""

from __future__ import annotations

from typing import Optional

from asm.ir.operands import Operand


class Instr:
    """Base de todas las instrucciones del IR."""

    line: str = ""

    def reads(self) -> list[Operand]:
        return []

    def writes(self) -> list[Operand]:
        return []

    def __repr__(self) -> str:
        return self.line or type(self).__name__


def _vals(*ops: Optional[Operand]) -> list[Operand]:
    return [o for o in ops if o is not None and not o.is_const]
