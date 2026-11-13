"""Arreglos: crear, longitud, leer y escribir un elemento."""

from __future__ import annotations

from dataclasses import dataclass

from asm.ir.base import Instr, _vals
from asm.ir.operands import Operand


@dataclass(repr=False)
class NewArray(Instr):
    """`x = newarray n`"""

    dst: Operand
    n: Operand  # cantidad de elementos
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.n)

    def writes(self) -> list[Operand]:
        return [self.dst]


@dataclass(repr=False)
class Len(Instr):
    """`x = len y`"""

    dst: Operand
    src: Operand
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.src)

    def writes(self) -> list[Operand]:
        return [self.dst]


@dataclass(repr=False)
class IndexLoad(Instr):
    """`x = base[idx]`. Si `base` es de tipo `vtable`, es el slot `idx` de la
    tabla de métodos (sin verificación de rango)."""

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
    """`base[idx] = src`"""

    base: Operand
    idx: Operand
    src: Operand
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.base, self.idx, self.src)
