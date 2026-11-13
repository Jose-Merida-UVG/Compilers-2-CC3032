"""`Instr`, la base de todas las instrucciones, y `_vals`."""

from __future__ import annotations

from typing import Optional

from asm.ir.operands import Operand


class Instr:
    """Base de las instrucciones. `line` es el TAC del que salió."""

    line: str = ""

    def reads(self) -> list[Operand]:
        """Operandos que lee (sin constantes). Los usa el asignador."""
        return []

    def writes(self) -> list[Operand]:
        """Operandos que escribe."""
        return []

    def __repr__(self) -> str:
        return self.line or type(self).__name__


def _vals(*ops: Optional[Operand]) -> list[Operand]:
    """Quita `None` y constantes: no ocupan registro."""
    return [o for o in ops if o is not None and not o.is_const]
