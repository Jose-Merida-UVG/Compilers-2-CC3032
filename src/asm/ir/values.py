"""Copia, operaciones unarias y binarias, y `print`."""

from __future__ import annotations

from dataclasses import dataclass

from asm.ir.base import Instr, _vals
from asm.ir.operands import Operand


@dataclass(repr=False)
class Copy(Instr):
    """`x = y`"""

    dst: Operand
    src: Operand
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.src)

    def writes(self) -> list[Operand]:
        return [self.dst]


@dataclass(repr=False)
class Unary(Instr):
    """`x = - y`, `x = ! y` o `x = itof y` (entero a float)."""

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
    """`x = a op b`"""

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
    """`print x`"""

    src: Operand
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.src)
