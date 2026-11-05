"""OpsSel: operaciones aritméticas, lógicas, comparaciones y `print` (Nes).

Contrato: docs/proyecto3/01-contrato.md §4 y §6. Solo se usa la API del
asignador (`regs.use`, `regs.def_`, `regs.scratch`, `regs.into`): ningún
selector nombra registros para valores. Los registros fijos que sí aparecen
(`$a0`, `$a1`, `$v0`, `$f12`) son los reservados del ABI del runtime.

Regla de oro: `regs.def_()` puede devolver el registro de un fuente que ya
murió, así que primero se leen los fuentes (`use`) y el destino se pide al
final; en cada instrucción el destino solo se escribe en la última.

Las comparaciones como valor usan solo instrucciones reales de MIPS (`slt`,
`sltu`, `sltiu`, `xori`, `subu`), sin pseudoinstrucciones de MARS cuya
expansión podría pisar un fuente si el destino coincide con él.
"""

from __future__ import annotations

from asm.ir import FLOAT, Binary, Operand, Print, Unary

IMM_MIN, IMM_MAX = -32768, 32767

FLOAT_ARITH = {"+": "add.s", "-": "sub.s", "*": "mul.s", "/": "div.s"}
COMPARISONS = ("==", "!=", "<", "<=", ">", ">=")


def is_imm(op: Operand) -> bool:
    """Constante entera/booleana que cabe en un inmediato de 16 bits."""
    return (
        op.is_const
        and op.ty.kind in ("int", "bool")
        and isinstance(op.value, (int, bool))
        and IMM_MIN <= int(op.value) <= IMM_MAX
    )


def as_float_operand(op: Operand) -> Operand:
    """Constante entera -> constante float (el TAC deja algunas sin convertir)."""
    value = float(op.value or 0)
    return Operand(repr(value), "const", FLOAT, value)


def as_float(gen, op: Operand) -> str:
    """Registro float con el valor de `op`, convirtiendo un entero si hace falta.

    Lo comparten `sel_ops`, `sel_control`, `sel_arrays` y `sel_calls`: un
    entero donde se espera un float (constante o variable) se convierte aquí
    con `mtc1` + `cvt.s.w`.
    """
    regs, asm = gen.regs, gen.a
    if op.is_const:
        return regs.use(op if op.ty.kind == "float" else as_float_operand(op))
    if op.is_float:
        return regs.use(op)
    ri = regs.use(op)
    rf = regs.scratch("float")
    asm.ins(f"mtc1  {ri}, {rf}")
    asm.ins(f"cvt.s.w {rf}, {rf}")
    return rf


def is_str(op: Operand) -> bool:
    return op.ty.kind == "str"


def pow2_shift(op: Operand):
    """k si `op` es la constante 2**k (k >= 1), si no None."""
    if op.is_const and op.ty.kind == "int" and isinstance(op.value, int):
        v = op.value
        if v >= 2 and v & (v - 1) == 0:
            return v.bit_length() - 1
    return None


class OpsSel:
    # ── unarios ────────────────────────────────────────────────────────────
    def sel_Unary(self, ins: Unary) -> None:
        regs, asm = self.regs, self.a
        if ins.op == "itof":
            if not ins.src.is_const and not ins.src.is_float:
                ri = regs.use(ins.src)
                rd = regs.def_(ins.dst)  # float: otra clase, no choca con `ri`
                asm.ins(f"mtc1  {ri}, {rd}")
                asm.ins(f"cvt.s.w {rd}, {rd}")
            else:  # constante o ya float: solo se copia
                rf = as_float(self, ins.src)
                rd = regs.def_(ins.dst)
                if rd != rf:
                    asm.ins(f"mov.s {rd}, {rf}")
        elif ins.op == "-":
            if ins.src.is_float or ins.dst.is_float:
                rs = as_float(self, ins.src)
                rd = regs.def_(ins.dst)
                asm.ins(f"neg.s {rd}, {rs}")
            else:
                rs = regs.use(ins.src)
                rd = regs.def_(ins.dst)
                asm.ins(f"subu  {rd}, $zero, {rs}")
        elif ins.op == "!":
            rs = regs.use(ins.src)
            rd = regs.def_(ins.dst)
            asm.ins(f"xori  {rd}, {rs}, 1")
        else:
            raise NotImplementedError(f"operador unario {ins.op!r}: {ins.line!r}")

    # ── binarios ───────────────────────────────────────────────────────────
    def sel_Binary(self, ins: Binary) -> None:
        a, b, op = ins.a, ins.b, ins.op
        if op in COMPARISONS:
            if is_str(a) and is_str(b):
                return self._str_equal_value(ins)
            if a.is_float or b.is_float:
                return self._float_compare_value(ins)
            return self._int_compare_value(ins)
        if op == "+" and (is_str(a) or is_str(b) or ins.dst.ty.kind == "str"):
            return self._concat(ins)
        if ins.dst.is_float or a.is_float or b.is_float:
            return self._float_arith(ins)
        return self._int_arith(ins)

    # -- enteros --------------------------------------------------------------
    def _int_arith(self, ins: Binary) -> None:
        regs, asm = self.regs, self.a
        a, b, op = ins.a, ins.b, ins.op
        if op in ("+", "*") and a.is_const and not b.is_const:
            a, b = b, a  # conmutativos: la constante a la derecha
        ra = regs.use(a)

        if op in ("+", "-") and is_imm(b):
            imm = int(b.value) if op == "+" else -int(b.value)
            if IMM_MIN <= imm <= IMM_MAX:
                rd = regs.def_(ins.dst)
                asm.ins(f"addiu {rd}, {ra}, {imm}")
                return
        if op == "*" and pow2_shift(b) is not None:
            rd = regs.def_(ins.dst)
            asm.ins(f"sll   {rd}, {ra}, {pow2_shift(b)}")
            return

        rb = regs.use(b)
        rd = regs.def_(ins.dst)
        if op == "+":
            asm.ins(f"addu  {rd}, {ra}, {rb}")
        elif op == "-":
            asm.ins(f"subu  {rd}, {ra}, {rb}")
        elif op == "*":
            asm.ins(f"mul   {rd}, {ra}, {rb}")
        elif op == "/":
            asm.ins(f"div   {ra}, {rb}")
            asm.ins(f"mflo  {rd}")
        elif op == "%":
            asm.ins(f"div   {ra}, {rb}")
            asm.ins(f"mfhi  {rd}")
        else:
            raise NotImplementedError(f"operador {op!r}: {ins.line!r}")

    def _int_compare_value(self, ins: Binary) -> None:
        regs, asm = self.regs, self.a
        ra, rb = regs.use(ins.a), regs.use(ins.b)
        rd = regs.def_(ins.dst)
        op = ins.op
        if op == "<":
            asm.ins(f"slt   {rd}, {ra}, {rb}")
        elif op == ">":
            asm.ins(f"slt   {rd}, {rb}, {ra}")
        elif op == "<=":  # a <= b  <=>  !(b < a)
            asm.ins(f"slt   {rd}, {rb}, {ra}")
            asm.ins(f"xori  {rd}, {rd}, 1")
        elif op == ">=":
            asm.ins(f"slt   {rd}, {ra}, {rb}")
            asm.ins(f"xori  {rd}, {rd}, 1")
        elif op == "==":
            asm.ins(f"subu  {rd}, {ra}, {rb}")
            asm.ins(f"sltiu {rd}, {rd}, 1")
        else:  # !=
            asm.ins(f"subu  {rd}, {ra}, {rb}")
            asm.ins(f"sltu  {rd}, $zero, {rd}")

    # -- floats ----------------------------------------------------------------
    def _float_arith(self, ins: Binary) -> None:
        regs, asm = self.regs, self.a
        if ins.op not in FLOAT_ARITH:
            raise NotImplementedError(f"operador {ins.op!r} sobre floats: {ins.line!r}")
        fa, fb = as_float(self, ins.a), as_float(self, ins.b)
        rd = regs.def_(ins.dst)
        asm.ins(f"{FLOAT_ARITH[ins.op]} {rd}, {fa}, {fb}")

    def _float_compare_value(self, ins: Binary) -> None:
        regs, asm = self.regs, self.a
        fa, fb = as_float(self, ins.a), as_float(self, ins.b)
        rd = regs.def_(ins.dst)
        cmp_ins, x, y, true_when_set = float_condition(ins.op, fa, fb)
        end = asm.new_label("fcmp")
        asm.ins(f"li    {rd}, {1 if true_when_set else 0}")
        asm.ins(f"{cmp_ins} {x}, {y}")
        asm.ins(f"bc1t  {end}")
        asm.ins(f"li    {rd}, {0 if true_when_set else 1}")
        asm.label(end)

    # -- strings ---------------------------------------------------------------
    def _concat(self, ins: Binary) -> None:
        regs, asm = self.regs, self.a
        regs.into("$a0", ins.a)
        regs.into("$a1", ins.b)
        asm.ins("jal   rt_str_concat")
        rd = regs.def_(ins.dst)
        asm.ins(f"move  {rd}, $v0")

    def _str_equal_value(self, ins: Binary) -> None:
        regs, asm = self.regs, self.a
        regs.into("$a0", ins.a)
        regs.into("$a1", ins.b)
        asm.ins("jal   rt_str_eq")
        rd = regs.def_(ins.dst)
        if ins.op == "==":
            asm.ins(f"move  {rd}, $v0")
        else:
            asm.ins(f"xori  {rd}, $v0, 1")

    # ── print ──────────────────────────────────────────────────────────────
    def sel_Print(self, ins: Print) -> None:
        regs, asm = self.regs, self.a
        kind = ins.src.ty.kind
        if kind == "float":
            regs.into("$f12", ins.src)
            asm.ins("jal   rt_print_float")
        elif kind == "bool":
            regs.into("$a0", ins.src)
            asm.ins("jal   rt_print_bool")
        elif kind == "str":
            regs.into("$a0", ins.src)
            asm.ins("jal   rt_print_str")
        else:  # int y, por omisión, cualquier otro valor
            regs.into("$a0", ins.src)
            asm.ins("jal   rt_print_int")


def float_condition(rel: str, fa: str, fb: str):
    """(instrucción de comparación, x, y, verdad_cuando_bandera_activa).

    MIPS solo compara `<`, `<=`, `==` en la FPU; `>` y `>=` intercambian los
    operandos y `!=` es la negación de `==`.
    """
    if rel == "<":
        return "c.lt.s", fa, fb, True
    if rel == "<=":
        return "c.le.s", fa, fb, True
    if rel == ">":
        return "c.lt.s", fb, fa, True
    if rel == ">=":
        return "c.le.s", fb, fa, True
    if rel == "==":
        return "c.eq.s", fa, fb, True
    if rel == "!=":
        return "c.eq.s", fa, fb, False
    raise NotImplementedError(f"comparación {rel!r}")
