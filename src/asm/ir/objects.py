"""Instrucciones de objetos: instancias, campos y tabla de métodos."""

from __future__ import annotations

from dataclasses import dataclass

from asm.ir.base import Instr, _vals
from asm.ir.operands import Operand


@dataclass(repr=False)
class FieldLoad(Instr):
    dst: Operand
    obj: Operand
    field: str
    offset: int = 0  # offset del campo según el layout de la clase estática
    fsize: int = 4  # tamaño del campo (1 si es boolean)
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.obj)

    def writes(self) -> list[Operand]:
        return [self.dst]


@dataclass(repr=False)
class FieldStore(Instr):
    obj: Operand
    field: str
    src: Operand
    offset: int = 0
    fsize: int = 4
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.obj, self.src)


@dataclass(repr=False)
class New(Instr):
    dst: Operand
    cls: str
    size: int = 4  # layout.size de la clase
    line: str = ""

    def writes(self) -> list[Operand]:
        return [self.dst]


@dataclass(repr=False)
class VTableLoad(Instr):
    dst: Operand
    obj: Operand
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.obj)

    def writes(self) -> list[Operand]:
        return [self.dst]
