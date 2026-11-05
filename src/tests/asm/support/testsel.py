"""Selectores mínimos de PRUEBA para ejercitar el driver (no son los reales).

Siguen el contrato (docs/proyecto3/01-contrato.md §2.3 y §4) y sirven de
ejemplo de cómo un selector usa `regs.use` / `regs.def_` / `regs.flush`. Los
selectores reales son `sel_ops.py`, `sel_control.py`, `sel_calls.py`…
"""

from __future__ import annotations

from asm.generator import AsmGenerator

class MiniSel:
    BIN = {"+":"addu","-":"subu","*":"mul","<":"slt",">":"sgt","<=":"sle",">=":"sge","==":"seq","!=":"sne"}
    def sel_Binary(self, ins):
        r, a = self.regs, self.a
        ra, rb = r.use(ins.a), r.use(ins.b)
        rd = r.def_(ins.dst)
        if ins.op in self.BIN: a.ins(f"{self.BIN[ins.op]} {rd}, {ra}, {rb}")
        elif ins.op == "/": a.ins(f"div {ra}, {rb}"); a.ins(f"mflo {rd}")
        elif ins.op == "%": a.ins(f"div {ra}, {rb}"); a.ins(f"mfhi {rd}")
    def sel_Print(self, ins):
        self.regs.into("$a0", ins.src); self.a.ins("jal rt_print_int")
    def sel_Goto(self, ins): self.a.ins(f"j {ins.label}")
    def sel_CondJump(self, ins):
        r, a = self.regs, self.a
        ra = r.use(ins.a)
        if ins.rel is None:
            a.ins(f"{'bne' if ins.sense=='if' else 'beq'} {ra}, $zero, {ins.label}")
        else:
            rb = r.use(ins.b)
            br = {"==":"beq","!=":"bne","<":"blt","<=":"ble",">":"bgt",">=":"bge"}[ins.rel]
            a.ins(f"{br} {ra}, {rb}, {ins.label}")
    def sel_Call(self, ins):
        r, a = self.regs, self.a
        n = len(ins.args)
        if n: a.ins(f"addiu $sp, $sp, -{4*n}")
        for i, arg in enumerate(ins.args):
            rs = r.use(arg); a.ins(f"sw {rs}, {4*i}($sp)")
        r.flush()
        a.ins(f"jal {self.fn_label(ins.callee)}")
        r.invalidate()
        if n: a.ins(f"addiu $sp, $sp, {4*n}")
        if ins.dst is not None:
            rd = r.def_(ins.dst); a.ins(f"move {rd}, $v0")
    def sel_Return(self, ins):
        if ins.src is not None: self.regs.into("$v0", ins.src)
        self.a.ins(f"j {self.fr.ret_label}")

class MiniGen(MiniSel, AsmGenerator):
    """Generador con los selectores mínimos de prueba."""

RUNTIME = ["rt_print_int:", "    li $v0, 1", "    syscall", "    li $v0, 11", "    li $a0, 10", "    syscall", "    jr $ra"]
