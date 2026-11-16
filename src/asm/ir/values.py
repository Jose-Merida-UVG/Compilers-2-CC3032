"""Copia, operaciones unarias y binarias, y `print`."""

from __future__ import annotations

from dataclasses import dataclass

from asm.ir.base import Instr
from asm.ir.operands import Operand


@dataclass(repr=False)
class Copy(Instr):
    """`x = y`"""

    READS = ("src",)
    WRITES = ("dst",)

    dst: Operand
    src: Operand
    line: str = ""


@dataclass(repr=False)
class Unary(Instr):
    """`x = - y`, `x = ! y` o `x = itof y` (entero a float)."""

    READS = ("src",)
    WRITES = ("dst",)

    dst: Operand
    op: str  # '-' | '!' | 'itof'
    src: Operand
    line: str = ""


@dataclass(repr=False)
class Binary(Instr):
    """`x = a op b`"""

    READS = ("a", "b")
    WRITES = ("dst",)

    dst: Operand
    a: Operand
    op: str  # + - * / % == != < <= > >=
    b: Operand
    line: str = ""


@dataclass(repr=False)
class Print(Instr):
    """`print x`"""

    READS = ("src",)

    src: Operand
    line: str = ""
