"""CallSel: llamadas a funciones y `return` (Nes).

Secuencia de llamada (contrato §2.3). Todo es *caller-saved*: no se usan `$s`.

        addiu $sp, $sp, -4*n          # n argumentos (en métodos, `this` es el 0)
        sw    r_i, 4*i($sp)           # swc1 si es float
        <flush>                       # todo lo sucio a su casa, ANTES de saltar
        jal   f_destino
        <invalidate>                  # tras la llamada ningún registro es confiable
        addiu $sp, $sp, 4*n
        move  rd, $v0                 # mov.s rd, $f0 si es float

El valor de retorno viaja en `$v0` (int, bool, string, referencias) o `$f0`
(float). Ninguna dirección de las "casas" es relativa a `$sp`, así que mover
`$sp` para empujar argumentos no invalida nada.

Las constantes se pasan por `$v1` / `$f12` (reservados) en lugar de ocupar un
registro del asignador: una llamada con muchos argumentos constantes no
agotaría el pool.
"""

from __future__ import annotations

from asm.ir import Call, Operand, Return
from asm.sel_ops import as_float, as_float_operand


class CallSel:
    # -- tipos conocidos del callee ------------------------------------------------
    def _param_is_float(self, ins: Call, i: int) -> bool:
        """¿El parámetro `i` del callee es float? En constructores y métodos el
        argumento 0 es `this`, que `func_types` no lista: se desplaza el índice."""
        types = self.program.func_types.get(ins.callee)
        if not types:
            return False
        k = i - max(0, len(ins.args) - len(types[0]))
        return 0 <= k < len(types[0]) and types[0][k].is_float

    def _returns_float(self, label: str) -> bool:
        types = self.program.func_types.get(label)
        return bool(types and types[1].is_float)

    # -- llamada ------------------------------------------------------------------
    def sel_Call(self, ins: Call) -> None:
        regs, asm = self.regs, self.a
        n = len(ins.args)
        if n:
            asm.ins(f"addiu $sp, $sp, -{4 * n}")
        for i, arg in enumerate(ins.args):
            self._store_arg(arg, 4 * i, arg.is_float or self._param_is_float(ins, i))

        regs.flush()
        asm.ins(f"jal   {self.fn_label(ins.callee)}")
        regs.invalidate()
        if n:
            asm.ins(f"addiu $sp, $sp, {4 * n}")

        if ins.dst is not None:
            rd = regs.def_(ins.dst)
            asm.ins(f"mov.s {rd}, $f0" if ins.dst.is_float else f"move  {rd}, $v0")

    def _store_arg(self, arg: Operand, offset: int, as_float_arg: bool) -> None:
        """Guarda un argumento en `offset($sp)`."""
        regs, asm = self.regs, self.a
        if as_float_arg:
            if arg.is_const:
                const = arg if arg.ty.kind == "float" else as_float_operand(arg)
                regs.into("$f12", const)
                reg = "$f12"
            else:
                reg = as_float(self, arg)
            asm.ins(f"swc1  {reg}, {offset}($sp)")
            return
        if arg.is_const:
            if arg.ty.kind != "str" and not arg.value:  # 0, false, null
                reg = "$zero"
            else:
                regs.into("$v1", arg)
                reg = "$v1"
        else:
            reg = regs.use(arg)
        asm.ins(f"sw    {reg}, {offset}($sp)")

    # -- return -------------------------------------------------------------------
    def sel_Return(self, ins: Return) -> None:
        """Valor a `$v0`/`$f0` y salto al epílogo (que es del marco). El driver
        ya hizo `flush()` antes de despachar el `Return`."""
        asm, regs = self.a, self.regs
        if ins.src is not None:
            src = ins.src
            if src.is_float or self._returns_float(self.fr.label):
                if src.is_const:
                    regs.into("$f0", src if src.ty.kind == "float" else as_float_operand(src))
                elif src.is_float:
                    regs.into("$f0", src)
                else:  # entero donde se espera float
                    rf = as_float(self, src)
                    asm.ins(f"mov.s $f0, {rf}")
            else:
                regs.into("$v0", src)
        asm.ins(f"j     {self.fr.ret_label}")
