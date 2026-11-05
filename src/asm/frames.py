"""Registros de activación: dónde vive cada valor y cómo se arma el marco.

Contrato: docs/proyecto3/01-contrato.md §2. La pila crece hacia abajo:

        fp+8+4*i   argumento i (i = 0 es el primer parámetro / `this`)
        fp+4       $ra guardado
        fp+0       $fp del llamador            <- $fp apunta aquí
        fp-4 ...   locales (locals_size)
        fp-(locals_size+4N)   temporal $tN (N desde 1)

Todas las "casas" se direccionan relativas a `$fp` o `$gp`, **nunca** a
`$sp`: así mover `$sp` al empujar argumentos no invalida ninguna dirección.

`FrameInfo.home(op)` es el único lugar que decide direcciones; los
selectores y el asignador de registros solo lo consultan.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from asm.emitter import AsmEmitter, mangle_func, mangle_ret
from asm.ir import FuncUnit, Operand

WORD = 4
SAVED = 8

_TEMP = re.compile(r"^\$t(\d+)$")


@dataclass(frozen=True)
class Home:
    """Casa en memoria de un valor: `offset($base)`."""

    base: str  # 'gp' | 'fp'
    offset: int
    size: int = 4

    def mem(self) -> str:
        return f"{self.offset}(${self.base})"

    @property
    def address(self) -> str:
        sign = "+" if self.offset >= 0 else "-"
        return f"{self.base}{sign}{abs(self.offset)}"


class FrameInfo:
    """Marco de activación de una función o método."""

    def __init__(self, unit: FuncUnit):
        self.unit = unit
        self.label = unit.label
        self.locals_size = int(unit.frame.get("locals_size", 0))
        self.temps = int(unit.frame.get("temps", 0))
        self.temps_size = WORD * self.temps
        self.alloc = self.locals_size + self.temps_size  # bytes bajo $fp
        self.fn_label = mangle_func(unit.label)
        self.ret_label = mangle_ret(unit.label)

    # -- casas -----------------------------------------------------------
    def temp_home(self, n: int) -> Home:
        return Home("fp", -(self.locals_size + WORD * n), WORD)

    def param_home(self, index: int) -> Home:
        return Home("fp", SAVED + WORD * index, WORD)

    def home(self, op: Operand) -> Home:
        if op.is_const:
            raise ValueError(f"{op.text}: una constante no tiene casa en memoria")
        m = _TEMP.match(op.text)
        if m:
            return self.temp_home(int(m.group(1)))
        if op.text in self.unit.params:
            return self.param_home(self.unit.params.index(op.text))
        sym = self.unit.symbols.get(op.text)
        if sym is None or not sym.get("address"):
            raise KeyError(f"{self.label}: '{op.text}' no tiene dirección en la tabla de símbolos")
        base, off = _parse_address(sym["address"])
        return Home(base, off, int(sym.get("size") or WORD))

    def mem(self, op: Operand) -> str:
        return self.home(op).mem()

    # -- prólogo / epílogo ----------------------------------------------
    def emit_prologue(self, asm: AsmEmitter) -> None:
        asm.label(self.fn_label)
        asm.ins("addiu $sp, $sp, -8")
        asm.ins("sw    $ra, 4($sp)")
        asm.ins("sw    $fp, 0($sp)")
        asm.ins("move  $fp, $sp")
        if self.alloc:
            asm.ins(f"addiu $sp, $sp, -{self.alloc}")

    def emit_epilogue(self, asm: AsmEmitter) -> None:
        asm.label(self.ret_label)
        asm.ins("move  $sp, $fp")
        asm.ins("lw    $ra, 4($sp)")
        asm.ins("lw    $fp, 0($sp)")
        asm.ins("addiu $sp, $sp, 8")
        asm.ins("jr    $ra")

    # -- datos para el IDE (los usa activation.py) -----------------------
    def slots(self) -> list[dict]:
        """Casillas del registro de activación, de direcciones altas a bajas.

        Cada una: {"name", "kind": param|saved|local|temp, "offset", "address",
        "size"}; `offset` es relativo a `$fp`.
        """
        slots: list[dict] = []

        def add(name: str, kind: str, home: Home) -> None:
            slots.append({
                "name": name, "kind": kind, "offset": home.offset,
                "address": home.address, "size": home.size,
            })

        for i, name in enumerate(self.unit.params):
            add(name, "param", self.param_home(i))
        add("$ra", "saved", Home("fp", 4, WORD))
        add("$fp", "saved", Home("fp", 0, WORD))
        for name, sym in self.unit.symbols.items():
            addr = sym.get("address") or ""
            if addr.startswith("fp-") and name not in self.unit.params:
                base, off = _parse_address(addr)
                add(name, "local", Home(base, off, int(sym.get("size") or WORD)))
        for n in range(1, self.temps + 1):
            add(f"$t{n}", "temp", self.temp_home(n))
        slots.sort(key=lambda s: -s["offset"])
        return slots


def _parse_address(address: str) -> tuple[str, int]:
    """`"gp+4"` -> ('gp', 4); `"fp-8"` -> ('fp', -8); `"fp+12"` -> ('fp', 12)."""
    m = re.match(r"^(gp|fp)([+-])(\d+)$", address)
    if not m:
        raise ValueError(f"dirección inesperada: {address!r}")
    off = int(m.group(3))
    return m.group(1), off if m.group(2) == "+" else -off
