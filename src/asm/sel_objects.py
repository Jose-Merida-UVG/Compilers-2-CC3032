"""ObjectSel: objetos, campos, tabla de métodos y llamadas virtuales (Tono).

Un objeto es `[tabla de métodos][campo0][campo1]…`. `New` reserva `size` bytes
y escribe en la palabra 0 la dirección de `vt_<Clase>`; `offset` y `fsize` de
los campos ya vienen resueltos del layout. La tabla (`emit_vtables`) tiene una
palabra por slot con la dirección del método.
"""

from __future__ import annotations

from asm.emitter import AsmEmitter, mangle_func, mangle_vtable
from asm.ir import Call, CallVirt, ClassUnit, FieldLoad, FieldStore, New, VTableLoad
from asm.sel_ops import as_float


class ObjectSel:
    def sel_New(self, ins: New) -> None:
        regs, asm = self.regs, self.a
        asm.ins(f"li    $a0, {ins.size}")
        asm.ins("jal   rt_alloc")  # solo toca $a0 y $v0: no hace falta flush
        asm.ins(f"la    $v1, {mangle_vtable(ins.cls)}")
        asm.ins("sw    $v1, 0($v0)")  # palabra 0: la tabla de métodos de la clase
        rd = regs.def_(ins.dst)
        asm.ins(f"move  {rd}, $v0")

    def sel_FieldLoad(self, ins: FieldLoad) -> None:
        regs, asm = self.regs, self.a
        ro = regs.use(ins.obj)
        rd = regs.def_(ins.dst)
        if ins.dst.is_float:
            load = "lwc1 "
        else:
            load = "lb   " if ins.fsize == 1 else "lw   "
        asm.ins(f"{load} {rd}, {ins.offset}({ro})")

    def sel_FieldStore(self, ins: FieldStore) -> None:
        regs, asm = self.regs, self.a
        ro = regs.use(ins.obj)
        if ins.ty.is_float or ins.src.is_float:
            rs = as_float(self, ins.src)  # un entero donde se espera float se convierte
            store = "swc1 "
        else:
            rs = regs.use(ins.src)
            store = "sb   " if ins.fsize == 1 else "sw   "
        asm.ins(f"{store} {rs}, {ins.offset}({ro})")

    def sel_VTableLoad(self, ins: VTableLoad) -> None:
        regs, asm = self.regs, self.a
        ro = regs.use(ins.obj)
        rd = regs.def_(ins.dst)
        asm.ins(f"lw    {rd}, 0({ro})")  # la tabla de métodos es la palabra 0

    def sel_CallVirt(self, ins: CallVirt) -> None:
        """Igual que `sel_Call` (sel_calls.py), pero salta a la dirección que
        está en un registro: la entrada de la tabla de métodos."""
        regs, asm = self.regs, self.a
        n = len(ins.args)
        rt = regs.use(ins.target)  # bloqueado hasta el final: sobrevive a los push
        if n:
            asm.ins(f"addiu $sp, $sp, -{4 * n}")
        # los tipos de los parámetros salen del método del tipo estático
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
