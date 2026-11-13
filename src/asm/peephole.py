"""Mirilla (peephole) sobre el MIPS ya generado (Tono).

Solo transformaciones que no cambian el comportamiento, buscadas entre
instrucciones contiguas (los comentarios `# TAC: ...` se saltan, las etiquetas
no, porque alguien puede saltar a ellas):

    move_redundante       `move $r, $r`                       se quita
    salto_a_la_siguiente  `j L` justo antes de `L:`           se quita el salto
    carga_tras_guardar    `sw $r, A` + `lw $r, A`             se quita el `lw`
                          (igual con `swc1` / `lwc1`)

`optimize(lines)` devuelve las líneas nuevas y cuántas veces se aplicó cada una.
"""

from __future__ import annotations

import re
from collections import Counter

_MOVE = re.compile(r"^move\s+(\$\w+),\s*(\$\w+)$")
_JUMP = re.compile(r"^j\s+([\w$.]+)$")
_LABEL = re.compile(r"^([\w$.]+):$")
_STORE = re.compile(r"^(sw|swc1)\s+(\$\w+),\s*(.+)$")
_LOAD = re.compile(r"^(lw|lwc1)\s+(\$\w+),\s*(.+)$")
_PAIR = {"sw": "lw", "swc1": "lwc1"}


def _code(line: str) -> str:
    """La línea sin comentario ni sangría."""
    return line.split("#", 1)[0].strip()


def _next(lines: list[str], i: int) -> int | None:
    """Índice de la siguiente línea que no es comentario ni está en blanco."""
    for j in range(i + 1, len(lines)):
        if _code(lines[j]):
            return j
    return None


def _label_follows(lines: list[str], i: int, target: str) -> bool:
    """¿`target:` aparece antes de cualquier instrucción? (otras etiquetas en
    medio no importan: caen igual a la misma instrucción)."""
    j = _next(lines, i)
    while j is not None:
        m = _LABEL.match(_code(lines[j]))
        if m is None:
            return False
        if m.group(1) == target:
            return True
        j = _next(lines, j)
    return False


def _pass(lines: list[str], changes: Counter) -> list[str]:
    drop: set[int] = set()
    for i, line in enumerate(lines):
        if i in drop:
            continue
        code = _code(line)

        m = _MOVE.match(code)
        if m and m.group(1) == m.group(2):
            drop.add(i)
            changes["move_redundante"] += 1
            continue

        m = _JUMP.match(code)
        if m and _label_follows(lines, i, m.group(1)):
            drop.add(i)
            changes["salto_a_la_siguiente"] += 1
            continue

        m = _STORE.match(code)
        if m:
            j = _next(lines, i)
            load = _LOAD.match(_code(lines[j])) if j is not None else None
            if (
                j is not None and load
                and load.group(1) == _PAIR[m.group(1)]
                and load.group(2) == m.group(2)
                and load.group(3) == m.group(3)
            ):
                drop.add(j)
                changes["carga_tras_guardar"] += 1
    return [line for i, line in enumerate(lines) if i not in drop]


def optimize(lines: list[str]) -> tuple[list[str], dict[str, int]]:
    changes: Counter = Counter()
    current = list(lines)
    for _ in range(5):  # quitar una cosa puede dejar otra al descubierto
        before = sum(changes.values())
        current = _pass(current, changes)
        if sum(changes.values()) == before:
            break
    return current, dict(changes)
