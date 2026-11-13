"""Instrucciones sobre valores: copia, operaciones y `print`."""

from __future__ import annotations

from dataclasses import dataclass

from asm.ir.base import Instr, _vals
from asm.ir.operands import Operand


@dataclass(repr=False)
class Copy(Instr):
    dst: Operand
    src: Operand
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.src)

    def writes(self) -> list[Operand]:
        return [self.dst]


@dataclass(repr=False)
class Unary(Instr):
    dst: Operand
    op: str  # '-' | '!' | 'itof'
    src: Operand
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.src)

    def writes(self) -> list[Operand]:
        return [self.dst]


@dataclass(repr=False)
class Binary(Instr):
    dst: Operand
    a: Operand
    op: str  # + - * / % == != < <= > >=
    b: Operand
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.a, self.b)

    def writes(self) -> list[Operand]:
        return [self.dst]


@dataclass(repr=False)
class Print(Instr):
    src: Operand
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.src)
