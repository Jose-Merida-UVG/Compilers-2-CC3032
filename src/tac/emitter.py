"""Emisión de TAC y reciclaje de temporales por unidad."""
from __future__ import annotations

from dataclasses import dataclass, field
import heapq
import re

from tac.instructions import (
    INDENT,
    LABEL_PREFIX,
    MAIN_NAME,
    TEMP_PREFIX,
    label_definition,
)


@dataclass
class _Unit:
    """Estado independiente de una función o clase."""

    name: str
    kind: str
    text: list[str]
    children: list[_Unit] = field(default_factory=list)
    free_indices: list[int] = field(default_factory=list)
    live_indices: set[int] = field(default_factory=set)
    next_index: int = 0
    peak: int = 0


class Emitter:
    def __init__(self) -> None:
        self._stack: list[_Unit] = []
        self._roots: list[_Unit] = []
        self._label_counter = 0
        self._max_temps: dict[str, int] = {}

    def _current(self) -> _Unit:
        if not self._stack:
            raise RuntimeError("No hay una unidad TAC abierta")
        return self._stack[-1]

    def emit(self, text: str) -> None:
        """Agrega una instrucción con cuatro espacios."""
        self._current().text.append(INDENT + text)

    def emit_label(self, label: str) -> None:
        """Agrega una etiqueta sin sangría."""
        self._current().text.append(label_definition(label))

    def new_label(self) -> str:
        """Las etiquetas son únicas en todo el programa."""
        self._label_counter += 1
        return f"{LABEL_PREFIX}{self._label_counter}"

    def new_temp(self) -> str:
        """Reutiliza el menor índice libre o crea uno nuevo."""
        unit = self._current()
        if unit.free_indices:
            index = heapq.heappop(unit.free_indices)
        else:
            unit.next_index += 1
            index = unit.next_index

        unit.live_indices.add(index)
        unit.peak = max(unit.peak, len(unit.live_indices))
        return f"{TEMP_PREFIX}{index}"

    def free(self, operand: str | None) -> None:
        """Libera un temporal vivo; otros operandos no hacen nada."""
        match = re.fullmatch(r"\$t([1-9]\d*)", operand or "")
        if match is None:
            return

        unit = self._current()
        index = int(match.group(1))
        if index in unit.live_indices:
            unit.live_indices.remove(index)
            heapq.heappush(unit.free_indices, index)

    def begin_unit(self, header: str) -> None:
        """Abre una unidad con su propio pool de temporales."""
        match = re.fullmatch(r"(func|class)\s+([^\s(:]+).*:", header)
        if match is None:
            raise ValueError(f"Cabecera TAC inválida: {header}")

        kind, name = match.groups()
        unit = _Unit(name=name, kind=kind, text=[header])

        if self._stack:
            self._stack[-1].children.append(unit)
        else:
            self._roots.append(unit)

        self._stack.append(unit)

    def end_unit(self, footer: str) -> None:
        """Cierra la unidad y verifica que no queden temporales vivos."""
        unit = self._current()
        if footer != f"end{unit.kind}":
            raise ValueError(f"Cierre incorrecto para {unit.name}: {footer}")

        if unit.live_indices:
            live = ", ".join(
                f"{TEMP_PREFIX}{index}"
                for index in sorted(unit.live_indices)
            )
            raise RuntimeError(
                f"Fuga de temporales en {unit.name}: {live}"
            )

        unit.text.append(footer)
        self._max_temps[unit.name] = unit.peak
        self._stack.pop()

    def max_temps(self, unit_name: str) -> int:
        """Pico de temporales simultáneos de la unidad indicada."""
        for unit in reversed(self._stack):
            if unit.name == unit_name:
                return unit.peak
        return self._max_temps.get(unit_name, 0)

    def live_temps(self) -> int:
        """Temporales vivos de la unidad actual; cero si no hay unidad."""
        if not self._stack:
            return 0
        return len(self._stack[-1].live_indices)

    def _render_unit(self, unit: _Unit) -> list[str]:
        children = [
            line
            for child in unit.children
            for line in self._render_unit(child)
        ]

        if unit.kind == "class":
            return unit.text[:-1] + children + unit.text[-1:]

        if unit.name == MAIN_NAME:
            return children + unit.text

        return unit.text + children

    def lines(self) -> list[str]:
        """Devuelve el TAC completo, con __main al final."""
        if self._stack:
            raise RuntimeError("Hay unidades TAC sin cerrar")

        units = [unit for unit in self._roots if unit.name != MAIN_NAME]
        units += [unit for unit in self._roots if unit.name == MAIN_NAME]
        return [
            line
            for unit in units
            for line in self._render_unit(unit)
        ]