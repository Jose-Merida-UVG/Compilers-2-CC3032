"""`Operand`: una variable, temporal o constante, con su tipo."""

from __future__ import annotations

from dataclasses import dataclass

from asm.ir.types import UNKNOWN, Ty


@dataclass
class Operand:
    """Un valor del TAC.

    text:  el TAC tal cual ("x", "x_1", "$t3", "5", "2.5", '"hola"', "true")
    kind:  'var' (tiene casa en memoria), 'temp' (muere tras su último uso)
           o 'const' (no tiene casa: el valor va dentro de la instrucción)
    ty:    tipo
    value: solo en 'const': int | float | bool | str (sin comillas) | None (null)
    size:  bytes que ocupa en memoria (1 si es un boolean)
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
        """Cómo lo reconoce el asignador de registros: por su texto."""
        return self.text

    def __repr__(self) -> str:
        return f"{self.text}:{self.ty}"
