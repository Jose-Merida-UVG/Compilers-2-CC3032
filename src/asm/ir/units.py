"""Funciones, clases y el programa completo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from asm.ir.base import Instr


@dataclass
class FuncUnit:
    """Una función o método (`func ... endfunc`).

    label:   etiqueta TAC ("fact", "Animal.hablar", "__main")
    params:  nombres de los parámetros en orden (`this` primero en métodos)
    body:    las instrucciones
    frame:   tamaños del marco: params_size, locals_size, temps, temps_size,
             saved_size, total_size
    symbols: nombre TAC -> {kind, type, address, size}, los de la función y
             luego los globales
    owner_class: clase a la que pertenece, si es un método
    """

    label: str
    params: list[str]
    body: list[Instr]
    frame: dict
    symbols: dict = field(default_factory=dict)
    owner_class: Optional[str] = None
    param_types: dict = field(default_factory=dict)  # parámetro -> Ty


@dataclass
class ClassUnit:
    """Una clase (`class ... endclass`) con sus métodos."""

    name: str
    parent: Optional[str]
    vtable: list[str]  # etiqueta del método de cada slot
    funcs: list[FuncUnit]
    layout: dict = field(default_factory=dict)


@dataclass
class Program:
    """El TAC completo."""

    units: list  # FuncUnit | ClassUnit, en el orden del TAC
    globals_size: int = 4  # bytes de variables globales
    classes: dict = field(default_factory=dict)  # nombre -> layout JSON
    func_types: dict = field(default_factory=dict)  # etiqueta -> (params, ret)
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
