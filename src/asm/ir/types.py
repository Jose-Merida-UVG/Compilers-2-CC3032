"""Tipos de los valores del TAC: int, float, bool, str, array, obj, vtable..."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Ty:
    """Tipo estático de un valor.

    kind: 'int' 'float' 'bool' 'str' 'array' 'obj' 'vtable' 'null' 'void'
          'unknown'
    `str`, `array`, `obj` y `vtable` son punteros: caben en un registro entero.
    """

    kind: str
    elem: Optional["Ty"] = None  # tipo de los elementos, solo en 'array'
    cls: Optional[str] = None  # nombre de la clase, solo en 'obj'

    @property
    def is_float(self) -> bool:
        return self.kind == "float"

    # Solo para depurar.
    def __str__(self) -> str:
        if self.kind == "array":
            return f"{self.elem}[]"
        if self.kind == "obj":
            return f"obj({self.cls})"
        return self.kind


# Los tipos que no llevan parámetros.
INT = Ty("int")
FLOAT = Ty("float")
BOOL = Ty("bool")
STR = Ty("str")
NULL = Ty("null")  # el literal `null`
VOID = Ty("void")  # una función que no devuelve nada
VTABLE = Ty("vtable")  # tabla de métodos de un objeto (`x = vtable obj`)
UNKNOWN = Ty("unknown")  # el parser no pudo deducirlo


def array_of(elem: Optional[Ty]) -> Ty:
    return Ty("array", elem=elem)


def obj_of(cls: str) -> Ty:
    return Ty("obj", cls=cls)
