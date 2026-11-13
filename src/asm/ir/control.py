"""Etiquetas, saltos y retorno."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from asm.ir.base import Instr, _vals
from asm.ir.operands import Operand


@dataclass(repr=False)
class Label(Instr):
    """`L1:`"""

    name: str
    line: str = ""


@dataclass(repr=False)
class Goto(Instr):
    """`goto L1`"""

    label: str
    line: str = ""


@dataclass(repr=False)
class CondJump(Instr):
    """`if a goto L`, `ifFalse a goto L` o `if a REL b goto L`."""

    sense: str  # 'if' | 'ifFalse'
    a: Operand
    rel: Optional[str]  # '<', '==', ...; None si solo se prueba `a`
    b: Optional[Operand]  # None si `rel` es None
    label: str
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.a, self.b)


@dataclass(repr=False)
class Return(Instr):
    """`return x` o `return`."""

    src: Optional[Operand]  # None si no devuelve valor
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.src)


# Terminan un bloque básico.
TERMINATORS = (Goto, CondJump, Return)
