"""Instrucciones de control de flujo: etiquetas, saltos y retorno."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from asm.ir.base import Instr, _vals
from asm.ir.operands import Operand


@dataclass(repr=False)
class Label(Instr):
    name: str
    line: str = ""


@dataclass(repr=False)
class Goto(Instr):
    label: str
    line: str = ""


@dataclass(repr=False)
class CondJump(Instr):
    """`if a goto L`, `ifFalse a goto L`, `if a REL b goto L`."""

    sense: str  # 'if' | 'ifFalse'
    a: Operand
    rel: Optional[str]  # None => se prueba `a` solo
    b: Optional[Operand]
    label: str
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.a, self.b)


@dataclass(repr=False)
class Return(Instr):
    src: Optional[Operand]
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.src)


TERMINATORS = (Goto, CondJump, Return)
