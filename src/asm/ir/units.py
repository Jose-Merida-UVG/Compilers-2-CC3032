"""Funciones, clases y el programa completo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from asm.ir.base import Instr


@dataclass
class FuncUnit:
    """Una función o método (`func ... endfunc`)."""

    label: str
    params: list[str]
    body: list[Instr]
    frame: dict
    symbols: dict = field(default_factory=dict)
    owner_class: Optional[str] = None
    param_types: dict = field(default_factory=dict)  # Parámetro -> Ty
    captured: list = field(default_factory=list)  # Variables propias que usa una función anidada


@dataclass
class ClassUnit:
    """Una clase (`class ... endclass`) con sus métodos."""

    name: str
    parent: Optional[str]
    vtable: list[str]  # Etiqueta del método de cada slot
    funcs: list[FuncUnit]
    layout: dict = field(default_factory=dict)


@dataclass
class Program:
    """El TAC completo."""

    units: list  # FuncUnit | ClassUnit, en el orden del TAC
    globals_size: int = 4  # Bytes de variables globales
    classes: dict = field(default_factory=dict)  # Nombre -> layout JSON
    func_types: dict = field(default_factory=dict)  # Etiqueta -> (params, ret)
    warnings: list = field(default_factory=list)

    def functions(self) -> list[FuncUnit]:
        """Todas las funciones y métodos, en orden de emisión."""
        out: list[FuncUnit] = []
        for unit in self.units:
            if isinstance(unit, ClassUnit):
                out.extend(unit.funcs)
            else:
                out.append(unit)
        return out

    def class_units(self) -> list[ClassUnit]:
        return [u for u in self.units if isinstance(u, ClassUnit)]
