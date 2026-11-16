"""Arreglos: crear, longitud, leer y escribir un elemento."""

from __future__ import annotations

from dataclasses import dataclass

from asm.ir.base import Instr
from asm.ir.operands import Operand


@dataclass(repr=False)
class NewArray(Instr):
    """`x = newarray n`"""

    READS = ("n",)
    WRITES = ("dst",)

    dst: Operand
    n: Operand  # Cantidad de elementos
    line: str = ""


@dataclass(repr=False)
class Len(Instr):
    """`x = len y`"""

    READS = ("src",)
    WRITES = ("dst",)

    dst: Operand
    src: Operand
    line: str = ""


@dataclass(repr=False)
class IndexLoad(Instr):
    """`x = base[idx]`, con verificación de rango."""

    READS = ("base", "idx")
    WRITES = ("dst",)

    dst: Operand
    base: Operand
    idx: Operand
    line: str = ""


@dataclass(repr=False)
class IndexStore(Instr):
    """`base[idx] = src`"""

    READS = ("base", "idx", "src")

    base: Operand
    idx: Operand
    src: Operand
    line: str = ""
