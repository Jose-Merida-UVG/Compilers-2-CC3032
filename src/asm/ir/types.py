"""Tipos estáticos de los valores del TAC."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Ty:
    """Tipo estático de un valor del TAC.

    kind: 'int' 'float' 'bool' 'str' 'array' 'obj' 'vtable' 'null' 'void'
          'unknown'
    """

    kind: str
    elem: Optional["Ty"] = None  # solo para 'array'
    cls: Optional[str] = None  # solo para 'obj'

    @property
    def is_float(self) -> bool:
        return self.kind == "float"

    # Motivos de debug, etc.
    def __str__(self) -> str:
        if self.kind == "array":
            return f"{self.elem}[]"
        if self.kind == "obj":
            return f"obj({self.cls})"
        return self.kind


INT = Ty("int")


FLOAT = Ty("float")


BOOL = Ty("bool")


STR = Ty("str")


NULL = Ty("null")


VOID = Ty("void")


VTABLE = Ty("vtable")


UNKNOWN = Ty("unknown")


def array_of(elem: Optional[Ty]) -> Ty:
    return Ty("array", elem=elem)


def obj_of(cls: str) -> Ty:
    return Ty("obj", cls=cls)
