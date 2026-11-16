"""Objetos: `new`, leer y escribir campos, y la tabla de métodos."""

from __future__ import annotations

from dataclasses import dataclass

from asm.ir.base import Instr
from asm.ir.operands import Operand
from asm.ir.types import UNKNOWN, Ty


@dataclass(repr=False)
class FieldLoad(Instr):
    """`x = obj.campo`"""

    READS = ("obj",)
    WRITES = ("dst",)

    dst: Operand
    obj: Operand
    field: str
    offset: int = 0  # offset del campo dentro del objeto (el layout de la clase)
    fsize: int = 4  # tamaño del campo (1 si es boolean)
    line: str = ""


@dataclass(repr=False)
class FieldStore(Instr):
    """`obj.campo = src`"""

    READS = ("obj", "src")

    obj: Operand
    field: str
    src: Operand
    offset: int = 0
    fsize: int = 4
    ty: Ty = UNKNOWN  # tipo del campo: decide si se guarda como float
    line: str = ""


@dataclass(repr=False)
class New(Instr):
    """`x = new Clase`: reserva el objeto y guarda su tabla de métodos en la
    palabra 0."""

    WRITES = ("dst",)

    dst: Operand
    cls: str
    size: int = 4  # bytes del objeto, tabla de métodos incluida
    line: str = ""


@dataclass(repr=False)
class VTableLoad(Instr):
    """`x = vtable obj`: la tabla de métodos del objeto (su palabra 0)."""

    READS = ("obj",)
    WRITES = ("dst",)

    dst: Operand
    obj: Operand
    line: str = ""


@dataclass(repr=False)
class VTableSlotLoad(Instr):
    """`x = t[k]` con `t` una tabla de métodos: la dirección del método del
    slot `k`. Sin cabecera ni verificación de rango."""

    READS = ("table",)
    WRITES = ("dst",)

    dst: Operand
    table: Operand  # de tipo `vtable`
    slot: int
    line: str = ""
