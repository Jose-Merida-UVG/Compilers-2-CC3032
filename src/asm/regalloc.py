"""Asignador de registros: `getReg()` del libro (Aho et al., §8.6.3).

  * `reg_op`: qué valor tiene cada registro.
  * `op_reg`: en qué registro está cada valor; `dirty` marca los que tienen un
    valor más nuevo que su casa en memoria.
  * Siguiente uso, calculado hacia atrás por bloque: un temporal sin uso
    futuro está muerto y no se guarda. Las variables nunca mueren.

Política caller-saved (sin `$s`): lo sucio y vivo se guarda al final de cada
bloque y antes de cada `jal`, y tras una etiqueta o llamada no se confía en
ningún registro. Así el `try/catch` desenrolla la pila sin restaurar registros.
"""

from __future__ import annotations

from typing import Callable, Optional

from asm.emitter import AsmEmitter
from asm.ir import (
    CondJump,
    Goto,
    Instr,
    Label,
    Operand,
    Return,
    TERMINATORS,
    Try,
)

# Pool del asignador; `$a*`, `$v*`, `$f0`, `$f12` y `$at` son de uso fijo.
INT_REGS = [f"$t{i}" for i in range(10)]
FLOAT_REGS = ["$f4", "$f6", "$f8", "$f10", "$f14", "$f16", "$f18"]

DEAD = 10**9  # No se vuelve a usar: la mejor víctima de un spill
LIVE_OUT = 10**6  # Vive al salir del bloque: uso lejano y desconocido


def is_temp(key: str) -> bool:
    """¿Es un temporal del TAC (`$t3`)?"""
    return key.startswith("$t")


def split_blocks(body: list[Instr]) -> list[list[Instr]]:
    """Parte el cuerpo en bloques básicos."""
    blocks: list[list[Instr]] = []
    cur: list[Instr] = []
    for ins in body:
        if isinstance(ins, Label) and cur:
            blocks.append(cur)
            cur = []
        cur.append(ins)
        if isinstance(ins, TERMINATORS):
            blocks.append(cur)
            cur = []
    if cur:
        blocks.append(cur)
    return blocks


def block_live_out(blocks: list[list[Instr]]) -> list[set[str]]:
    """Temporales vivos al salir de cada bloque (flujo de datos hacia atrás)."""
    label_block: dict[str, int] = {}
    for i, blk in enumerate(blocks):
        if blk and isinstance(blk[0], Label):
            label_block[blk[0].name] = i

    succs: list[list[int]] = []
    for i, blk in enumerate(blocks):
        out: list[int] = []
        last = blk[-1]
        if isinstance(last, Goto):
            out.append(label_block[last.label])
        elif isinstance(last, CondJump):
            out.append(label_block[last.label])
            if i + 1 < len(blocks):
                out.append(i + 1)
        elif isinstance(last, Return):
            pass
        elif i + 1 < len(blocks):
            out.append(i + 1)
        for ins in blk:
            if isinstance(ins, Try) and ins.label in label_block:
                out.append(label_block[ins.label])
        succs.append(out)

    gen: list[set[str]] = []
    kill: list[set[str]] = []
    for blk in blocks:
        g: set[str] = set()
        k: set[str] = set()
        for ins in blk:
            for r in ins.reads():
                if is_temp(r.key) and r.key not in k:
                    g.add(r.key)
            for w in ins.writes():
                if is_temp(w.key):
                    k.add(w.key)
        gen.append(g)
        kill.append(k)

    live_in = [set() for _ in blocks]
    live_out = [set() for _ in blocks]
    changed = True
    while changed:
        changed = False
        for i in reversed(range(len(blocks))):
            out: set[str] = set()
            for s in succs[i]:
                out |= live_in[s]
            inn = gen[i] | (out - kill[i])
            if out != live_out[i] or inn != live_in[i]:
                live_out[i], live_in[i] = out, inn
                changed = True
    return live_out


class RegAlloc:
    """`getReg()` y sus descriptores; uno por función."""

    def __init__(self, asm: AsmEmitter, home: Callable[[Operand], object]):
        self.asm = asm
        self._home = home  # Operand -> Home (frames.FrameInfo.home)
        self.trace: list[dict] = []
        self._reset()
        self._block: list[Instr] = []
        self._nu: list[dict[str, int]] = []
        self._cur = 0
        self._alloc_reason = "libre"

    def _reset(self) -> None:
        """Vacía los descriptores: ningún registro tiene nada."""
        self.reg_op: dict[str, Operand] = {}  # Descriptor de registros
        self.op_reg: dict[str, str] = {}  # Descriptor de direcciones (parte reg.)
        self.dirty: set[str] = set()
        self.locked: set[str] = set()
        self.scratch_regs: list[str] = []

    def start_block(self, instrs: list[Instr], live_out: Optional[set[str]] = None) -> None:
        """Calcula el siguiente uso de cada valor y deja los registros vacíos."""
        self._reset()
        self._block = instrs
        state: dict[str, int] = {k: LIVE_OUT for k in (live_out or set())}
        nu: list[dict[str, int]] = [dict() for _ in instrs]
        for i in reversed(range(len(instrs))):
            nu[i] = dict(state)  # Info DESPUÉS de la instrucción i
            for w in instrs[i].writes():
                state.pop(w.key, None)
            for r in instrs[i].reads():
                state[r.key] = i
        self._nu = nu
        self._cur = 0

    def begin_instr(self, index: int) -> None:
        """Marca cuál instrucción del bloque se está traduciendo."""
        self._cur = index

    def next_use(self, key: str) -> int:
        """Siguiente uso de `key` después de la instrucción actual."""
        if self._cur < len(self._nu):
            v = self._nu[self._cur].get(key)
            if v is not None:
                return v
        return DEAD if is_temp(key) else LIVE_OUT

    def _line(self) -> str:
        """La línea TAC de la instrucción actual (para la traza y los errores)."""
        if self._cur < len(self._block):
            return self._block[self._cur].line
        return ""

    def _record(self, op: str, reg: str, reason: str) -> None:
        """Anota una decisión de `getReg` para la vista del IDE."""
        self.trace.append({"instr": self._line(), "op": op, "reg": reg, "reason": reason})

    @staticmethod
    def _cls(op: Operand) -> str:
        """Clase de registro que necesita un operando: `float` o `int`."""
        return "float" if op.is_float else "int"

    @staticmethod
    def _reg_cls(reg: str) -> str:
        """Clase de un registro: `$f*` es `float`, el resto `int`."""
        return "float" if reg.startswith("$f") else "int"

    def _load(self, reg: str, op: Operand) -> None:
        """Carga el valor de `op` desde su casa (`lwc1`, `lb` o `lw`)."""
        h = self._home(op)
        if op.is_float:
            self.asm.ins(f"lwc1  {reg}, {h.mem()}")
        elif h.size == 1:
            self.asm.ins(f"lb    {reg}, {h.mem()}")
        else:
            self.asm.ins(f"lw    {reg}, {h.mem()}")

    def _store(self, reg: str, op: Operand) -> None:
        """Guarda `reg` en la casa de `op` (`swc1`, `sb` o `sw`)."""
        h = self._home(op)
        if op.is_float:
            self.asm.ins(f"swc1  {reg}, {h.mem()}")
        elif h.size == 1:
            self.asm.ins(f"sb    {reg}, {h.mem()}")
        else:
            self.asm.ins(f"sw    {reg}, {h.mem()}")

    def _drop(self, reg: str) -> None:
        """Olvida lo que tenía `reg`, sin guardarlo."""
        op = self.reg_op.pop(reg, None)
        if op is not None:
            self.op_reg.pop(op.key, None)
        self.dirty.discard(reg)

    def _alloc(self, cls: str, avoid: tuple = ()) -> str:
        """Entrega un registro de la clase `cls`."""
        pool = INT_REGS if cls == "int" else FLOAT_REGS
        in_use = self.locked | set(self.scratch_regs) | set(avoid)
        for reg in pool:  # 1) un registro libre
            if reg not in self.reg_op and reg not in in_use:
                self._alloc_reason = "libre"
                return reg
        # 2) spill: la víctima con el siguiente uso más lejano (o ninguno)
        best, best_nu = None, -1
        for reg in pool:
            if reg in in_use:
                continue
            nu = self.next_use(self.reg_op[reg].key)
            if nu > best_nu:
                best, best_nu = reg, nu
        if best is None:
            raise RuntimeError(
                f"sin registros {cls} disponibles en: {self._line()!r} "
                "(la instrucción necesita más registros que el pool)"
            )
        victim = self.reg_op[best]
        if best in self.dirty and self.next_use(victim.key) != DEAD:
            self._store(best, victim)
        self._record(victim.key, best, "spill")
        self._drop(best)
        self._alloc_reason = "spill"
        return best

    def use(self, op: Operand) -> str:
        """Registro con el valor de `op` (lo carga de su casa si hace falta)."""
        if op.is_const:
            return self._const_reg(op)
        cls = self._cls(op)
        reg = self.op_reg.get(op.key)
        if reg is not None and self._reg_cls(reg) != cls:
            self._drop(reg)
            reg = None
        if reg is not None:
            self.locked.add(reg)
            self._record(op.key, reg, "en registro")
            return reg
        reg = self._alloc(cls)
        self._load(reg, op)
        self.reg_op[reg] = op
        self.op_reg[op.key] = reg
        self.locked.add(reg)
        self._record(op.key, reg, "carga")
        return reg

    def def_(self, op: Operand, avoid: tuple = ()) -> str:
        """Registro donde se calculará el nuevo valor de `op`."""
        cls = self._cls(op)
        reg = self.op_reg.get(op.key)
        if reg is not None and (self._reg_cls(reg) != cls or reg in avoid):
            self._drop(reg)
            reg = None
        reason = "mismo registro"
        if reg is None:
            for cand in sorted(self.locked):  # Operandos fuente de esta instrucción
                src = self.reg_op.get(cand)
                if (src is not None and cand not in avoid
                        and self._reg_cls(cand) == cls
                        and is_temp(src.key) and self.next_use(src.key) == DEAD):
                    self._drop(cand)  # Su valor murió: no hace falta guardarlo
                    reg, reason = cand, "reuso"
                    break
        if reg is None:
            reg = self._alloc(cls, avoid)
            reason = self._alloc_reason
        self.reg_op[reg] = op
        self.op_reg[op.key] = reg
        self.dirty.add(reg)
        self.locked.add(reg)
        self._record(op.key, reg, reason)
        return reg

    def scratch(self, cls: str = "int") -> str:
        """Registro anónimo hasta el final de la instrucción."""
        reg = self._alloc(cls)
        self.scratch_regs.append(reg)
        self._record("<scratch>", reg, self._alloc_reason)
        return reg

    def _const_reg(self, op: Operand) -> str:
        """Registro con el valor de una constante."""
        if op.ty.kind != "float" and op.ty.kind != "str" and op.value in (0, False, None):
            return "$zero"
        if op.ty.kind == "float":
            reg = self.scratch("float")
            self.asm.ins(f"l.s   {reg}, {self.asm.float_(float(op.value))}")
            return reg
        reg = self.scratch("int")
        self._load_const(reg, op)
        return reg

    def _load_const(self, reg: str, op: Operand) -> None:
        """Carga una constante que no es float."""
        if op.ty.kind == "str":
            self.asm.ins(f"la    {reg}, {self.asm.string(op.text)}")
        elif op.ty.kind == "bool":
            self.asm.ins(f"li    {reg}, {1 if op.value else 0}")
        elif op.value is None:
            self.asm.ins(f"li    {reg}, 0")
        else:
            self.asm.ins(f"li    {reg}, {int(op.value)}")

    def into(self, target: str, op: Operand) -> None:
        """Deja el valor de `op` en un registro fijo como `$a0`."""
        if op.is_const:
            if op.ty.kind == "float":
                self.asm.ins(f"l.s   {target}, {self.asm.float_(float(op.value))}")
            else:
                self._load_const(target, op)
            return
        reg = self.op_reg.get(op.key)
        if reg is not None and self._reg_cls(reg) == self._cls(op):
            self.asm.ins(f"mov.s {target}, {reg}" if op.is_float else f"move  {target}, {reg}")
        else:
            self._load(target, op)

    def flush(self) -> None:
        """Guarda a su casa todo lo sucio que sigue vivo (no invalida)."""
        for reg in sorted(self.dirty):
            op = self.reg_op[reg]
            if self.next_use(op.key) != DEAD:
                self._store(reg, op)
        self.dirty.clear()

    def invalidate(self) -> None:
        """Olvida todos los registros (tras una etiqueta o una llamada)."""
        if self.dirty:  # Por seguridad: nada vivo se pierde
            self._record("<flush implícito>", "-", "flush")
            self.flush()
        self.reg_op.clear()
        self.op_reg.clear()
        self.locked.clear()
        self.scratch_regs.clear()

    def end_instr(self, ins: Optional[Instr] = None) -> None:
        """Libera scratch y los registros de temporales que ya murieron."""
        self.locked.clear()
        self.scratch_regs.clear()
        for reg in list(self.reg_op):
            op = self.reg_op[reg]
            if is_temp(op.key) and self.next_use(op.key) == DEAD:
                self._drop(reg)
