"""Operandos: variables, temporales y constantes del TAC."""

from __future__ import annotations

from dataclasses import dataclass

from asm.ir.types import UNKNOWN, Ty


@dataclass
class Operand:
    """Un valor del TAC: variable, temporal o constante.

    text:  tal cual en el TAC ("x", "x_1", "$t3", "5", "2.5", '"hola"', "true")
    kind:  'var' | 'temp' | 'const'
    ty:    tipo estático
    value: para 'const': int | float | bool | str (sin comillas) | None (null)
    size:  bytes que ocupa en memoria (1 si es un boolean con casa de 1 byte)
    """

    text: str
    kind: str
    ty: Ty = UNKNOWN
    value: object = None
    size: int = 4

    @property
    def is_const(self) -> bool:
        return self.kind == "const"

    @property
    def is_temp(self) -> bool:
        return self.kind == "temp"

    @property
    def is_float(self) -> bool:
        return self.ty.kind == "float"

    @property
    def key(self) -> str:
        """Identidad del valor en el asignador de registros."""
        return self.text

    def __repr__(self) -> str:
        return f"{self.text}:{self.ty}"
