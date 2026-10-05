"""Layout de memoria para las fases de TAC y MIPS: tamaños, offsets, registros
de activación y layout de clases, calculados sobre el árbol de ámbitos.

Convenciones (MIPS32):
  * Tamaños: integer 4, float 4, boolean 1; string, arreglo, instancia,
    función y null son referencias de 4. Alineación natural, y cada área
    (parámetros, locales, objeto) se redondea a múltiplo de 4.
  * Globales (ámbito global y bloques directos): `gp+offset`.
  * Registro de activación (la pila crece hacia abajo), de direcciones altas
    a bajas:
        parámetros      fp+8+offset (el primero en la menor dirección; en un
                        método `this` ocupa el offset 0)
        ra guardado     fp+4
        fp guardado     fp+0
        locales         fp-(offset+tamaño), un espacio por símbolo
        temporales      4 bytes cada uno
  * `frame.total_size` = params + locals + temps + saved.
  * Clases: `this+0` guarda el puntero a la tabla de métodos de la clase; los
    campos heredados van después, en los offsets del padre; dirección de un
    campo `this+offset`. Las constantes también son campos.
  * Tabla de métodos (`vtable_entries`): un slot por método, con los del padre
    primero; un método sobrescrito reutiliza el slot del ancestro. Los
    constructores no entran (se llaman de forma estática).
  * Etiquetas: funciones `f`, métodos `Clase.metodo`, clases `Clase`.

`max_temps` (opcional) es `Emitter.max_temps` y llena `frame.temps` una vez
generado el TAC.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from semantic.symbols import Scope, ScopeKind, Symbol, SymbolKind
from semantic.types import BooleanType, ClassType, Type

WORD = 4
SAVED_SIZE = 8  # fp guardado (fp+0) y dirección de retorno (fp+4)

_DATA_KINDS = (SymbolKind.VARIABLE, SymbolKind.CONSTANT)


def size_of(type_: Type) -> int:
    return 1 if isinstance(type_, BooleanType) else WORD


def vtable_entries(class_type: ClassType) -> list[tuple[str, str]]:
    """Tabla de métodos de una clase: `(método, etiqueta)` por slot. Los slots
    del padre van primero y un método sobrescrito reemplaza la etiqueta en el
    mismo slot, así `slot(m)` es igual en toda la jerarquía."""
    entries: list[tuple[str, str]] = []
    if class_type.parent is not None:
        entries = vtable_entries(class_type.parent)
    for name, symbol in class_type.members.items():
        if symbol.kind is not SymbolKind.FUNCTION or name == "constructor":
            continue
        label = f"{class_type.class_name}.{name}"
        for slot, (existing, _) in enumerate(entries):
            if existing == name:
                entries[slot] = (name, label)
                break
        else:
            entries.append((name, label))
    return entries


def method_slot(class_type: ClassType, name: str) -> Optional[int]:
    """Slot de `name` en la tabla de `class_type`, o None si no es virtual."""
    for slot, (method, _) in enumerate(vtable_entries(class_type)):
        if method == name:
            return slot
    return None


def _align(offset: int, size: int) -> int:
    return -(-offset // size) * size


def _round_word(size: int) -> int:
    return _align(size, WORD)


@dataclass
class _Area:
    """Cursor sobre un área: globales, locales de un frame o campos."""

    used: int = 0

    def place(self, symbol: Symbol) -> int:
        size = size_of(symbol.type)
        offset = _align(self.used, size)
        self.used = offset + size
        symbol.size = size
        symbol.offset = offset
        return offset


class _Layout:
    def __init__(self, global_scope: Scope, max_temps: Optional[Callable[[str], int]]):
        self.max_temps = max_temps
        # ClassType.members es el mismo dict que los símbolos del ámbito de la
        # clase: su id lleva de un ClassType a su ámbito
        self.class_scopes: dict[int, Scope] = {}
        self.class_layouts: dict[int, dict] = {}
        self._collect_classes(global_scope)

    def _collect_classes(self, scope: Scope) -> None:
        if scope.kind is ScopeKind.CLASS:
            self.class_scopes[id(scope.symbols)] = scope
        for child in scope.children:
            self._collect_classes(child)

    def walk(self, scope: Scope, area: _Area, global_data: bool) -> None:
        """Coloca los símbolos de datos de `scope` en `area`; las funciones y
        clases anidadas llevan su propio frame o layout y los bloques
        comparten `area`."""
        for symbol in scope.symbols.values():
            self._set_label(symbol, scope)
            if symbol.kind in _DATA_KINDS:
                offset = area.place(symbol)
                if global_data:
                    symbol.address = f"gp+{offset}"
                else:
                    symbol.address = f"fp-{offset + size_of(symbol.type)}"

        for child in scope.children:
            if child.kind is ScopeKind.FUNCTION:
                self.function(child, scope)
            elif child.kind is ScopeKind.CLASS:
                self.cls(child)
            else:
                self.walk(child, area, global_data)

    @staticmethod
    def _set_label(symbol: Symbol, scope: Scope) -> None:
        if symbol.kind is SymbolKind.FUNCTION:
            owner = scope.owner if scope.kind is ScopeKind.CLASS else None
            symbol.label = f"{owner}.{symbol.name}" if owner else symbol.name
        elif symbol.kind is SymbolKind.CLASS:
            symbol.label = symbol.name

    def function(self, scope: Scope, enclosing: Scope) -> None:
        is_method = enclosing.kind is ScopeKind.CLASS
        name = scope.owner or "?"
        label = f"{enclosing.owner}.{name}" if is_method else name

        params = _Area(WORD if is_method else 0)  # `this` ocupa el offset 0
        for symbol in scope.symbols.values():
            if symbol.kind is SymbolKind.PARAMETER:
                offset = params.place(symbol)
                symbol.address = f"fp+{SAVED_SIZE + offset}"

        # Bajo un ámbito de función solo cuelgan bloques, funciones y clases
        locals_ = _Area()
        for child in scope.children:
            if child.kind is ScopeKind.FUNCTION:
                self.function(child, scope)
            elif child.kind is ScopeKind.CLASS:
                self.cls(child)
            else:
                self.walk(child, locals_, global_data=False)

        scope.frame = self._frame(label, params.used, locals_.used)

    def _frame(self, label: str, params_used: int, locals_used: int) -> dict:
        temps = self.max_temps(label) if self.max_temps else 0
        params_size = _round_word(params_used)
        locals_size = _round_word(locals_used)
        return {
            "label": label,
            "params_size": params_size,
            "locals_size": locals_size,
            "temps": temps,
            "temps_size": temps * WORD,
            "saved_size": SAVED_SIZE,
            "total_size": params_size + locals_size + temps * WORD + SAVED_SIZE,
        }

    @staticmethod
    def _class_symbol(scope: Scope) -> Optional[Symbol]:
        if scope.parent is None or scope.owner is None:
            return None
        return scope.parent.symbols.get(scope.owner)

    def _parent_scope(self, scope: Scope) -> Optional[Scope]:
        """Ámbito de la clase padre, o None."""
        class_symbol = self._class_symbol(scope)
        if class_symbol is None or not isinstance(class_symbol.type, ClassType):
            return None
        parent = class_symbol.type.parent
        return self.class_scopes.get(id(parent.members)) if parent else None

    def cls(self, scope: Scope) -> dict:
        key = id(scope)
        if key in self.class_layouts:
            return self.class_layouts[key]

        fields: list[dict] = []
        offset = WORD  # this+0: puntero a la tabla de métodos
        parent_name: Optional[str] = None
        parent_scope = self._parent_scope(scope)
        if parent_scope is not None:
            # El padre se calcula primero para heredar sus offsets
            parent_layout = self.cls(parent_scope)
            parent_name = parent_scope.owner
            fields = [dict(f, inherited=True) for f in parent_layout["fields"]]
            offset = parent_layout["size"]

        class_symbol = self._class_symbol(scope)
        class_type = (
            class_symbol.type
            if class_symbol is not None and isinstance(class_symbol.type, ClassType)
            else None
        )
        area = _Area(offset)
        methods: list[dict] = []
        for symbol in scope.symbols.values():
            self._set_label(symbol, scope)
            if symbol.kind in _DATA_KINDS:
                placed = area.place(symbol)
                symbol.address = f"this+{placed}"
                fields.append(
                    {
                        "name": symbol.name,
                        "offset": placed,
                        "size": symbol.size,
                        "inherited": False,
                    }
                )
            elif symbol.kind is SymbolKind.FUNCTION:
                methods.append(
                    {
                        "name": symbol.name,
                        "label": symbol.label,
                        "slot": method_slot(class_type, symbol.name) if class_type else None,
                        "overrides": self._overridden(scope, symbol.name),
                    }
                )

        layout = {
            "size": _round_word(area.used),
            "parent": parent_name,
            "fields": fields,
            "methods": methods,
            "vtable": [
                {"slot": slot, "name": name, "label": label}
                for slot, (name, label) in enumerate(
                    vtable_entries(class_type) if class_type else []
                )
            ],
        }
        scope.layout = layout
        self.class_layouts[key] = layout

        if class_symbol is not None:
            class_symbol.size = layout["size"]

        for child in scope.children:
            if child.kind is ScopeKind.FUNCTION:
                self.function(child, scope)
        return layout

    def _overridden(self, scope: Scope, method: str) -> Optional[str]:
        """Etiqueta del método del ancestro más cercano que este reemplaza.
        Un constructor nunca cuenta como sobrescritura."""
        if method == "constructor":
            return None
        ancestor = self._parent_scope(scope)
        while ancestor is not None:
            found = ancestor.symbols.get(method)
            if found is not None and found.kind is SymbolKind.FUNCTION:
                return f"{ancestor.owner}.{method}"
            ancestor = self._parent_scope(ancestor)
        return None


def _name_symbols(scope: Scope, tac_name: Callable[[Symbol], str]) -> None:
    for symbol in scope.symbols.values():
        symbol.tac_name = tac_name(symbol)
    for child in scope.children:
        _name_symbols(child, tac_name)


def assign_layout(
    global_scope: Scope,
    max_temps: Optional[Callable[[str], int]] = None,
    tac_name: Optional[Callable[[Symbol], str]] = None,
) -> None:
    """Llena size/offset/address/label de cada símbolo, `frame` de cada ámbito
    FUNCTION y `layout` de cada ámbito CLASS, en el lugar. El código de nivel
    superior es la función `__main`: su frame cuelga del ámbito global (sus
    variables son globales, así que solo guarda temporales y ra/fp).
    `tac_name` (el `name_of` del generador) da el nombre de cada símbolo en el
    TAC, que difiere del original cuando hay sombreado (`x_1`)."""
    layout = _Layout(global_scope, max_temps)
    layout.walk(global_scope, _Area(), global_data=True)
    global_scope.frame = layout._frame("__main", 0, 0)
    if tac_name is not None:
        _name_symbols(global_scope, tac_name)
