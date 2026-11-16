"""Emisor de MIPS: acumula `.data` y `.text` y nombra etiquetas.

Los selectores escriben con `ins`, `label`, `comment`, `string`, `float_`,
`data` y `new_label`. Las `mangle_*` convierten nombres del TAC en etiquetas
válidas (`Animal.hablar` -> `f_Animal__hablar`).
"""

from __future__ import annotations

import re

INDENT = "    "


def mangle_func(name: str) -> str:
    """Nombre MIPS de una función."""
    return "f_" + name.replace(".", "__")


def mangle_ret(name: str) -> str:
    """Etiqueta del epílogo de una función."""
    return mangle_func(name) + "__ret"


def mangle_vtable(cls: str) -> str:
    """Etiqueta de la tabla de métodos de una clase: `Animal` -> `vt_Animal`."""
    return "vt_" + cls


def mangle_tac_label(label: str) -> str:
    """Las etiquetas del TAC son únicas en el programa y se emiten igual."""
    return label


class AsmEmitter:
    """Acumula el `.data` y el `.text` del programa."""

    def __init__(self, tac_comments: bool = True) -> None:
        self.tac_comments = tac_comments
        self._text: list[str] = []
        self._data: list[str] = []
        self._strings: dict[str, str] = {}
        self._floats: dict[float, str] = {}
        self._label_counter = 0

    def ins(self, text: str) -> None:
        """`add $t0, $t1, $t2` (se agrega con sangría)."""
        self._text.append(INDENT + text)

    def label(self, name: str) -> None:
        """Etiqueta en `.text`."""
        self._text.append(f"{name}:")

    def comment(self, text: str) -> None:
        """Comentario en `.text`, con la misma sangría que las instrucciones."""
        self._text.append(f"{INDENT}# {text}")

    def tac_comment(self, text: str) -> None:
        """Comentario con la línea TAC de la que sale el código siguiente."""
        if self.tac_comments:
            self.comment(f"TAC: {text.strip()}")

    def directive(self, text: str) -> None:
        """Directiva del ensamblador en `.text` (`.align`, `.globl`...)."""
        self._text.append(f"{INDENT}{text}")

    def data(self, line: str) -> None:
        """Línea cruda en `.data` (vtables, mensajes del runtime)."""
        self._data.append(line)

    def string(self, literal: str) -> str:
        """Registra un literal string y devuelve su etiqueta."""
        if literal not in self._strings:
            label = f"str_{len(self._strings)}"
            self._strings[literal] = label
            self._data.append(f"{label}: .asciiz {literal}")
        return self._strings[literal]

    def float_(self, value: float) -> str:
        """Registra una constante float en `.data` y devuelve su etiqueta."""
        if value not in self._floats:
            label = f"flt_{len(self._floats)}"
            self._floats[value] = label
            self._data.append(f"{label}: .float {value!r}")
        return self._floats[value]

    def new_label(self, kind: str) -> str:
        """Etiqueta única `__<kind>_<n>` para saltos internos de un selector."""
        self._label_counter += 1
        return f"__{kind}_{self._label_counter}"

    def lines(self) -> list[str]:
        """El `.s` completo: `.data` y luego `.text`."""
        out = ["        .data"]
        out += self._data
        out += ["", "        .text", "        .globl main"]
        out += self._text
        return out


_SAFE = re.compile(r"[^A-Za-z0-9_]")


def safe_ident(text: str) -> str:
    """Convierte cualquier texto en un identificador válido de MIPS."""
    return _SAFE.sub("_", text)
