"""Objetos: `new`, leer y escribir campos, cargar la tabla de métodos."""

from __future__ import annotations

from dataclasses import dataclass

from asm.ir.base import Instr, _vals
from asm.ir.operands import Operand
from asm.ir.types import UNKNOWN, Ty


@dataclass(repr=False)
class FieldLoad(Instr):
    """`x = obj.campo`"""

    dst: Operand
    obj: Operand
    field: str
    offset: int = 0  # offset del campo dentro del objeto (el layout de la clase)
    fsize: int = 4  # tamaño del campo (1 si es boolean)
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.obj)

    def writes(self) -> list[Operand]:
        return [self.dst]


@dataclass(repr=False)
class FieldStore(Instr):
    """`obj.campo = src`"""

    obj: Operand
    field: str
    src: Operand
    offset: int = 0
    fsize: int = 4
    ty: Ty = UNKNOWN  # tipo del campo: decide si se guarda como float
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.obj, self.src)


@dataclass(repr=False)
class New(Instr):
    """`x = new Clase`: reserva el objeto y guarda su tabla de métodos en la
    palabra 0."""

    dst: Operand
    cls: str
    size: int = 4  # bytes del objeto, tabla de métodos incluida
    line: str = ""

    def writes(self) -> list[Operand]:
        return [self.dst]


@dataclass(repr=False)
class VTableLoad(Instr):
    """`x = vtable obj`: la tabla de métodos del objeto (su palabra 0)."""

    dst: Operand
    obj: Operand
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.obj)

    def writes(self) -> list[Operand]:
        return [self.dst]
