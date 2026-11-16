"""Selector de objetos: `new`, campos y llamadas virtuales.

Un objeto es `[tabla de métodos][campo0][campo1]...`; los offsets vienen del
layout del P2. Una llamada virtual son tres instrucciones del TAC: `vtable obj`,
`t[k]` y `callvirt`.
"""

from __future__ import annotations

from asm.emitter import AsmEmitter, mangle_func, mangle_vtable
from asm.ir import (
    Call, CallVirt, ClassUnit, FieldLoad, FieldStore, New, Operand, VTableLoad, VTableSlotLoad,
)
from asm.sel_ops import as_float


class ObjectSel:
    """Selector de objetos."""

    def _null_check(self, reg: str, obj: Operand) -> None:
        """Lanza si el objeto es `null`. `this` nunca lo es."""
        if obj.text != "this":
            self.a.ins(f"beq   {reg}, $zero, rt_throw_null")

    def sel_New(self, ins: New) -> None:
        """`x = new Clase`."""
        regs, asm = self.regs, self.a
        asm.ins(f"li    $a0, {ins.size}")
        asm.ins("jal   rt_alloc")  # Solo toca $a0 y $v0: no hace falta flush
        asm.ins(f"la    $v1, {mangle_vtable(ins.cls)}")
        asm.ins("sw    $v1, 0($v0)")  # Palabra 0: la tabla de métodos de la clase
        rd = regs.def_(ins.dst)
        asm.ins(f"move  {rd}, $v0")

    def sel_FieldLoad(self, ins: FieldLoad) -> None:
        """`x = obj.campo`: carga desde `offset(obj)` (`lb` si es boolean)."""
        regs, asm = self.regs, self.a
        ro = regs.use(ins.obj)
        self._null_check(ro, ins.obj)
        rd = regs.def_(ins.dst)
        if ins.dst.is_float:
            load = "lwc1 "
        else:
            load = "lb   " if ins.fsize == 1 else "lw   "
        asm.ins(f"{load} {rd}, {ins.offset}({ro})")

    def sel_FieldStore(self, ins: FieldStore) -> None:
        """`obj.campo = src`: guarda en `offset(obj)` (`sb` si es boolean)."""
        regs, asm = self.regs, self.a
        ro = regs.use(ins.obj)
        self._null_check(ro, ins.obj)
        if ins.ty.is_float or ins.src.is_float:
            rs = as_float(self, ins.src)  # Un entero donde se espera float se convierte
            store = "swc1 "
        else:
            rs = regs.use(ins.src)
            store = "sb   " if ins.fsize == 1 else "sw   "
        asm.ins(f"{store} {rs}, {ins.offset}({ro})")

    def sel_VTableLoad(self, ins: VTableLoad) -> None:
        """`t = vtable obj`: la tabla de métodos del objeto."""
        regs, asm = self.regs, self.a
        ro = regs.use(ins.obj)
        self._null_check(ro, ins.obj)
        rd = regs.def_(ins.dst)
        asm.ins(f"lw    {rd}, 0({ro})")  # La tabla de métodos es la palabra 0

    def sel_VTableSlotLoad(self, ins: VTableSlotLoad) -> None:
        """Entrada `slot` de la tabla de métodos."""
        regs, asm = self.regs, self.a
        rt = regs.use(ins.table)
        rd = regs.def_(ins.dst)
        asm.ins(f"lw    {rd}, {4 * ins.slot}({rt})")

    def sel_CallVirt(self, ins: CallVirt) -> None:
        """Igual que `sel_Call` (sel_calls.py), pero salta a la dirección que está en un registro."""
        regs, asm = self.regs, self.a
        n = len(ins.args)
        rt = regs.use(ins.target)  # Bloqueado hasta el final: sobrevive a los push
        if n:
            asm.ins(f"addiu $sp, $sp, -{4 * n}")
        # Los tipos de los parámetros salen del método del tipo estático
        shape = Call(ins.dst, ins.static_target or "", ins.args)
        for i, arg in enumerate(ins.args):
            self._store_arg(arg, 4 * i, arg.is_float or self._param_is_float(shape, i))

        regs.flush()
        asm.ins(f"jalr  {rt}")
        regs.invalidate()
        if n:
            asm.ins(f"addiu $sp, $sp, {4 * n}")

        if ins.dst is not None:
            rd = regs.def_(ins.dst)
            asm.ins(f"mov.s {rd}, $f0" if ins.dst.is_float else f"move  {rd}, $v0")


def emit_vtables(asm: AsmEmitter, classes: list[ClassUnit]) -> None:
    """Una tabla `vt_<Clase>` en `.data` por clase: la dirección de cada método."""
    for unit in classes:
        words = ", ".join(mangle_func(label) for label in unit.vtable) or "0"
        asm.data("        .align 2")
        asm.data(f"{mangle_vtable(unit.name)}: .word {words}")
