"""`try`, `endtry` y `catch`."""

from __future__ import annotations

from dataclasses import dataclass

from asm.ir.base import Instr
from asm.ir.operands import Operand


@dataclass(repr=False)
class Try(Instr):
    """`try L`: abre la región protegida; si algo falla dentro, salta a `L`."""

    label: str
    line: str = ""


@dataclass(repr=False)
class EndTry(Instr):
    """`endtry`: cierra la región protegida."""

    line: str = ""


@dataclass(repr=False)
class Catch(Instr):
    """`catch e`: primera línea del manejador; `e` recibe el mensaje (string)."""

    var: Operand
    line: str = ""

    def writes(self) -> list[Operand]:
        return [self.var]
