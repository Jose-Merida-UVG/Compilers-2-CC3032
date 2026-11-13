"""Emisor de MIPS: secciones `.data` / `.text`, etiquetas y nombres seguros.

Ver docs/proyecto3/01-contrato.md §1 y §5. Los selectores nunca arman el
archivo a mano: llaman a `ins`, `label`, `comment`, `string`, `float_`, `data`
y `new_label`.
"""

from __future__ import annotations

import re

INDENT = "    "


# Reemplaza . por _ y agrega el prefijo f_ para funciones.
def mangle_func(name: str) -> str:
    """`fact` -> `f_fact`; `Animal.hablar` -> `f_Animal__hablar`;
    `__main` -> `f___main`."""
    return "f_" + name.replace(".", "__")


def mangle_ret(name: str) -> str:
    """Etiqueta del epílogo de una función."""
    return mangle_func(name) + "__ret"


def mangle_vtable(cls: str) -> str:
    return "vt_" + cls


def mangle_tac_label(label: str) -> str:
    """Las etiquetas del TAC (`L12`) son únicas en todo el programa y se
    emiten tal cual."""
    return label


class AsmEmitter:
    """Acumula el `.data` y el `.text` de un programa."""

    def __init__(self, tac_comments: bool = True) -> None:
        self.tac_comments = tac_comments
        self._text: list[str] = []
        self._data: list[str] = []
        self._strings: dict[str, str] = {}
        self._floats: dict[float, str] = {}
        self._label_counter = 0

    # -- .text -----------------------------------------------------------
    def ins(self, text: str) -> None:
        """`add $t0, $t1, $t2` (se agrega con sangría)."""
        self._text.append(INDENT + text)

    def label(self, name: str) -> None:
        self._text.append(f"{name}:")

    def comment(self, text: str) -> None:
        self._text.append(f"{INDENT}# {text}")

    def tac_comment(self, text: str) -> None:
        """Comentario con la línea TAC de la que sale el código siguiente."""
        if self.tac_comments:
            self.comment(f"TAC: {text.strip()}")

    def directive(self, text: str) -> None:
        self._text.append(f"{INDENT}{text}")

    # -- .data -----------------------------------------------------------
    def data(self, line: str) -> None:
        """Línea cruda en `.data` (vtables, mensajes del runtime)."""
        self._data.append(line)

    def string(self, literal: str) -> str:
        """Registra un literal string y devuelve su etiqueta.

        `literal` es el texto del TAC con comillas (`"hola"`); se deduplica.
        """
        if literal not in self._strings:
            label = f"str_{len(self._strings)}"
            self._strings[literal] = label
            self._data.append(f"{label}: .asciiz {literal}")
        return self._strings[literal]

    def float_(self, value: float) -> str:
        if value not in self._floats:
            label = f"flt_{len(self._floats)}"
            self._floats[value] = label
            self._data.append(f"{label}: .float {value!r}")
        return self._floats[value]

    # -- etiquetas internas ----------------------------------------------
    def new_label(self, kind: str) -> str:
        """Etiqueta única `__<kind>_<n>` para saltos internos de un selector."""
        self._label_counter += 1
        return f"__{kind}_{self._label_counter}"

    # -- resultado -------------------------------------------------------
    def lines(self) -> list[str]:
        out = ["        .data"]
        out += self._data
        out += ["", "        .text", "        .globl main"]
        out += self._text
        return out


_SAFE = re.compile(r"[^A-Za-z0-9_]")


def safe_ident(text: str) -> str:
    """Convierte cualquier texto en un identificador válido de MIPS."""
    return _SAFE.sub("_", text)
