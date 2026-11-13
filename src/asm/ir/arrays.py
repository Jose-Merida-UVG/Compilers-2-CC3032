"""Instrucciones de arreglos."""

from __future__ import annotations

from dataclasses import dataclass

from asm.ir.base import Instr, _vals
from asm.ir.operands import Operand


@dataclass(repr=False)
class NewArray(Instr):
    dst: Operand
    n: Operand
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.n)

    def writes(self) -> list[Operand]:
        return [self.dst]


@dataclass(repr=False)
class Len(Instr):
    dst: Operand
    src: Operand
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.src)

    def writes(self) -> list[Operand]:
        return [self.dst]


@dataclass(repr=False)
class IndexLoad(Instr):
    dst: Operand
    base: Operand
    idx: Operand
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.base, self.idx)

    def writes(self) -> list[Operand]:
        return [self.dst]


@dataclass(repr=False)
class IndexStore(Instr):
    base: Operand
    idx: Operand
    src: Operand
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.base, self.idx, self.src)
