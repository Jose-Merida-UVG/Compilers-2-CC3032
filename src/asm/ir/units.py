"""Unidades del programa: funciones, clases y el programa completo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from asm.ir.base import Instr


@dataclass
class FuncUnit:
    """Una función o método.

    label:   etiqueta TAC ("fact", "Animal.hablar", "__main")
    params:  nombres de los parámetros en orden (incluye `this` en métodos)
    body:    instrucciones
    frame:   {"params_size","locals_size","temps","temps_size","saved_size",
              "total_size"} (temps ya incluye los temporales realmente usados)
    symbols: tac_name -> {"kind","type","address","size"} visibles en la
             unidad (los de la propia función primero, luego los globales)
    owner_class: nombre de la clase si es un método
    """

    label: str
    params: list[str]
    body: list[Instr]
    frame: dict
    symbols: dict = field(default_factory=dict)
    owner_class: Optional[str] = None
    param_types: dict = field(default_factory=dict)


@dataclass
class ClassUnit:
    name: str
    parent: Optional[str]
    vtable: list[str]  # etiquetas TAC de los métodos, por slot
    funcs: list[FuncUnit]
    layout: dict = field(default_factory=dict)


@dataclass
class Program:
    units: list  # FuncUnit | ClassUnit, en el orden del TAC
    globals_size: int = 4
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
