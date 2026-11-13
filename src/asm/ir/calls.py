"""Llamadas directas y virtuales."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from asm.ir.base import Instr, _vals
from asm.ir.operands import Operand


@dataclass(repr=False)
class Call(Instr):
    """`x = call f, n` (o `call f, n`), con sus `param` ya reunidos en `args`."""

    dst: Optional[Operand]  # None si se descarta el resultado
    callee: str  # etiqueta TAC ("fact", "Animal.hablar")
    args: list[Operand]  # en métodos, `this` es el primero
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(*self.args)

    def writes(self) -> list[Operand]:
        return [self.dst] if self.dst is not None else []


@dataclass(repr=False)
class CallVirt(Instr):
    """`x = callvirt t, n`: llamada indirecta, `t` tiene la dirección del método."""

    dst: Optional[Operand]
    target: Operand
    args: list[Operand]
    static_target: Optional[str] = None  # método según el tipo estático, solo para tipos
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.target, *self.args)

    def writes(self) -> list[Operand]:
        return [self.dst] if self.dst is not None else []
