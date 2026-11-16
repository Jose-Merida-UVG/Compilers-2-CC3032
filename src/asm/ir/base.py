"""`Instr`, la base de todas las instrucciones, y `non_const`."""

from __future__ import annotations

from typing import ClassVar, Optional

from asm.ir.operands import Operand


def non_const(*ops: Optional[Operand]) -> list[Operand]:
    """Quita `None` y constantes: no ocupan registro."""
    return [o for o in ops if o is not None and not o.is_const]


class Instr:
    """Base de las instrucciones. `line` es el TAC del que salió.

    Cada subclase declara con `READS` y `WRITES` los *nombres de los campos*
    que lee y escribe (un campo puede ser un operando, `None` o una lista de
    operandos). De ahí salen `reads()` y `writes()`, que el asignador usa para
    calcular el siguiente uso de cada valor.
    """

    line: str = ""
    READS: ClassVar[tuple[str, ...]] = ()
    WRITES: ClassVar[tuple[str, ...]] = ()

    def _operands(self, names: tuple[str, ...]) -> list[Optional[Operand]]:
        out: list[Optional[Operand]] = []
        for name in names:
            value = getattr(self, name)
            out.extend(value if isinstance(value, list) else [value])
        return out

    def reads(self) -> list[Operand]:
        """Operandos que lee (sin constantes)."""
        return non_const(*self._operands(self.READS))

    def writes(self) -> list[Operand]:
        """Operandos que escribe."""
        return [o for o in self._operands(self.WRITES) if o is not None]

    def __repr__(self) -> str:
        return self.line or type(self).__name__
