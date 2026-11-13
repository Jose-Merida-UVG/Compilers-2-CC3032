"""Instrucciones de regiones protegidas (`try` / `catch`)."""

from __future__ import annotations

from dataclasses import dataclass

from asm.ir.base import Instr
from asm.ir.operands import Operand


@dataclass(repr=False)
class Try(Instr):
    label: str
    line: str = ""


@dataclass(repr=False)
class EndTry(Instr):
    line: str = ""


@dataclass(repr=False)
class Catch(Instr):
    var: Operand
    line: str = ""

    def writes(self) -> list[Operand]:
        return [self.var]
