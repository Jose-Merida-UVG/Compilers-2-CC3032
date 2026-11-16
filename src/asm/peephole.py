"""Mirilla (peephole) sobre el MIPS ya generado.

Solo transformaciones que no cambian el comportamiento, buscadas entre
instrucciones contiguas (los comentarios `# TAC: ...` se saltan, las etiquetas
no, porque alguien puede saltar a ellas):

    move_redundante       `move $r, $r`                       se quita
    salto_a_la_siguiente  `j L` justo antes de `L:`           se quita el salto
    carga_tras_guardar    `sw $r, A` + `lw $r, A`             se quita el `lw`
                          (igual con `swc1` / `lwc1`)
    guardar_tras_cargar   `lw $r, A` + `sw $r, A`             se quita el `sw`
                          (si `$r` no es la base de `A`)
    identidad_aritmetica  `addiu $r,$r,0`, `addu $r,$r,$zero`,
                          `sll $r,$r,0`, `ori $r,$r,0`        se quita
    move_ida_y_vuelta     `move a, b` + `move b, a`           se quita el segundo
    salto_sobre_salto     `beq x,y,L1` + `j L2` + `L1:`       `bne x,y,L2` + `L1:`
    codigo_muerto         instrucciones entre un `j`/`jr` y   se quitan
                          la siguiente etiqueta

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
_RPAIR = {"lw": "sw", "lwc1": "swc1"}
_IDENT = re.compile(
    r"^(?:addiu\s+(\$\w+),\s*\1,\s*0|addu\s+(\$\w+),\s*\2,\s*\$zero"
    r"|sll\s+(\$\w+),\s*\3,\s*0|ori\s+(\$\w+),\s*\4,\s*0)$"
)
_BRANCH = re.compile(r"^(beq|bne)\s+(\$\w+),\s*(\$\w+),\s*([\w$.]+)$")
_INVERSE = {"beq": "bne", "bne": "beq"}
_BARRIER = re.compile(r"^(j\s+[\w$.]+|jr\s+\$\w+)$")


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


def _is_instruction(code: str) -> bool:
    return bool(code) and not code.endswith(":") and not code.startswith(".")


def _pass(lines: list[str], changes: Counter) -> list[str]:
    drop: set[int] = set()
    repl: dict[int, str] = {}
    for i, line in enumerate(lines):
        if i in drop:
            continue
        code = _code(line)

        if _IDENT.match(code):
            drop.add(i)
            changes["identidad_aritmetica"] += 1
            continue

        m = _MOVE.match(code)
        if m and m.group(1) == m.group(2):
            drop.add(i)
            changes["move_redundante"] += 1
            continue
        if m:
            j = _next(lines, i)
            back = _MOVE.match(_code(lines[j])) if j is not None else None
            if back and back.group(1) == m.group(2) and back.group(2) == m.group(1):
                drop.add(j)
                changes["move_ida_y_vuelta"] += 1

        m = _BRANCH.match(code)
        if m:
            j = _next(lines, i)
            jump = _JUMP.match(_code(lines[j])) if j is not None else None
            if jump and _label_follows(lines, j, m.group(4)):
                indent = lines[i][: len(lines[i]) - len(lines[i].lstrip())]
                repl[i] = (f"{indent}{_INVERSE[m.group(1)]}   {m.group(2)}, "
                           f"{m.group(3)}, {jump.group(1)}")
                drop.add(j)
                changes["salto_sobre_salto"] += 1
                continue

        if _BARRIER.match(code):
            k = _next(lines, i)
            while k is not None and _is_instruction(_code(lines[k])):
                drop.add(k)
                changes["codigo_muerto"] += 1
                k = _next(lines, k)

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

        m = _LOAD.match(code)
        if m and m.group(1) in _RPAIR:
            j = _next(lines, i)
            store = _STORE.match(_code(lines[j])) if j is not None else None
            if (
                store
                and store.group(1) == _RPAIR[m.group(1)]
                and store.group(2) == m.group(2)
                and store.group(3) == m.group(3)
                and m.group(2) not in m.group(3)  # `lw $t0, 0($t0)` cambia la dirección
            ):
                drop.add(j)
                changes["guardar_tras_cargar"] += 1
    return [repl.get(i, line) for i, line in enumerate(lines) if i not in drop]


def optimize(lines: list[str]) -> tuple[list[str], dict[str, int]]:
    changes: Counter = Counter()
    current = list(lines)
    for _ in range(5):  # quitar una cosa puede dejar otra al descubierto
        before = sum(changes.values())
        current = _pass(current, changes)
        if sum(changes.values()) == before:
            break
    return current, dict(changes)
