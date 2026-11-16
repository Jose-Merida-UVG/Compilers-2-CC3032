"""Selector de control de flujo: `Label`, `Goto` y `CondJump`.

Los `if`, `while`, `for`, `switch`, `break`... ya son etiquetas y saltos en el
TAC. El driver hace flush antes del salto, así que la condición se lee de los
registros sin recargar.
"""

from __future__ import annotations

from asm.ir import CondJump, Goto, Label
from asm.sel_ops import as_float, float_condition, is_str

BRANCH = {"==": "beq", "!=": "bne", "<": "blt", "<=": "ble", ">": "bgt", ">=": "bge"}
NEGATE = {"==": "!=", "!=": "==", "<": ">=", "<=": ">", ">": "<=", ">=": "<"}
# Contra cero hay instrucciones reales que no necesitan cargar el cero
BRANCH_ZERO = {"<": "bltz", "<=": "blez", ">": "bgtz", ">=": "bgez"}


def is_zero(op) -> bool:
    """¿Es la constante 0 o `false`?"""
    return op.is_const and op.ty.kind in ("int", "bool") and not op.value


class ControlSel:
    """Selector de control de flujo."""

    def sel_Label(self, ins: Label) -> None:
        """Escribe la etiqueta. El driver ya vació los registros del bloque."""
        self.a.label(ins.name)

    def sel_Goto(self, ins: Goto) -> None:
        """Salto incondicional."""
        self.a.ins(f"j     {ins.label}")

    def sel_CondJump(self, ins: CondJump) -> None:
        """Salto condicional."""
        take_if_true = ins.sense == "if"  # 'ifFalse' salta cuando la condición es falsa
        if ins.rel is None:
            return self._jump_on_value(ins, take_if_true)
        a, b = ins.a, ins.b
        if ins.rel in ("==", "!=") and is_str(a) and is_str(b):
            return self._jump_on_str_eq(ins, take_if_true)
        if a.is_float or b.is_float:
            return self._jump_on_float(ins, take_if_true)
        return self._jump_on_int(ins, take_if_true)

    # `if x goto L` / `ifFalse x goto L`
    def _jump_on_value(self, ins: CondJump, take_if_true: bool) -> None:
        """Salta según si un valor booleano es distinto de cero."""
        a = ins.a
        if a.is_const:  # La condición se decide en compilación
            if bool(a.value) == take_if_true:
                self.a.ins(f"j     {ins.label}")
            return
        ra = self.regs.use(a)
        self.a.ins(f"{'bne' if take_if_true else 'beq'}   {ra}, $zero, {ins.label}")

    # `if a REL b goto L` con enteros, booleanos, null y referencias
    def _jump_on_int(self, ins: CondJump, take_if_true: bool) -> None:
        """Una sola rama; contra cero usa `bltz`, `bgez`..."""
        regs, asm = self.regs, self.a
        rel = ins.rel if take_if_true else NEGATE[ins.rel]
        if is_zero(ins.b) and rel in BRANCH_ZERO:
            ra = regs.use(ins.a)
            asm.ins(f"{BRANCH_ZERO[rel]} {ra}, {ins.label}")
            return
        ra, rb = regs.use(ins.a), regs.use(ins.b)
        asm.ins(f"{BRANCH[rel]}   {ra}, {rb}, {ins.label}")

    def _jump_on_float(self, ins: CondJump, take_if_true: bool) -> None:
        """Compara floats."""
        asm = self.a
        fa, fb = as_float(self, ins.a), as_float(self, ins.b)
        cmp_ins, x, y, true_when_set = float_condition(ins.rel, fa, fb)
        asm.ins(f"{cmp_ins} {x}, {y}")
        branch_on_set = take_if_true == true_when_set
        asm.ins(f"{'bc1t' if branch_on_set else 'bc1f'}  {ins.label}")

    def _jump_on_str_eq(self, ins: CondJump, take_if_true: bool) -> None:
        """`==` o `!=` entre strings: `rt_str_eq` devuelve 1 si son iguales."""
        regs, asm = self.regs, self.a
        regs.into("$a0", ins.a)
        regs.into("$a1", ins.b)
        asm.ins("jal   rt_str_eq")
        # $v0 = 1 si son iguales: para `==` la condición es ($v0 != 0)
        jump_when_equal = (ins.rel == "==") == take_if_true
        asm.ins(f"{'bne' if jump_when_equal else 'beq'}   $v0, $zero, {ins.label}")
