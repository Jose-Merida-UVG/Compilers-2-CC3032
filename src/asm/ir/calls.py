"""Llamadas directas y virtuales."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from asm.ir.base import Instr
from asm.ir.operands import Operand


@dataclass(repr=False)
class Call(Instr):
    """`x = call f, n` (o `call f, n`), con sus `param` ya reunidos en `args`."""

    READS = ("args",)
    WRITES = ("dst",)

    dst: Optional[Operand]  # None si se descarta el resultado
    callee: str  # etiqueta TAC ("fact", "Animal.hablar")
    args: list[Operand]  # en métodos, `this` es el primero
    line: str = ""


@dataclass(repr=False)
class CallVirt(Instr):
    """`x = callvirt t, n`: llamada indirecta, `t` tiene la dirección del método."""

    READS = ("target", "args")
    WRITES = ("dst",)

    dst: Optional[Operand]
    target: Operand
    args: list[Operand]
    # el método que corresponde al tipo estático del receptor; lo usan los tipos
    # de los parámetros (sel_objects) y el árbol de activación (activation.py)
    static_target: Optional[str] = None
    line: str = ""
