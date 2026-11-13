"""Llamadas a funciones y llamadas virtuales."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from asm.ir.base import Instr, _vals
from asm.ir.operands import Operand


@dataclass(repr=False)
class Call(Instr):
    dst: Optional[Operand]
    callee: str  # etiqueta TAC ("fact", "Animal.hablar")
    args: list[Operand]  # ya agrupados; len(args) == n
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(*self.args)

    def writes(self) -> list[Operand]:
        return [self.dst] if self.dst is not None else []


@dataclass(repr=False)
class CallVirt(Instr):
    dst: Optional[Operand]
    target: Operand  # contiene la dirección del método
    args: list[Operand]
    static_target: Optional[str] = None  # etiqueta resuelta por el tipo estático
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.target, *self.args)

    def writes(self) -> list[Operand]:
        return [self.dst] if self.dst is not None else []
