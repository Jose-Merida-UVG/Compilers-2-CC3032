"""CoreSel: selección de instrucciones para declaración y asignación.

`let x = 5;`, `x = y;`, `const K = "hola";` llegan al TAC como `x = y` o
`x = constante` (una `Copy` en el IR). Las declaraciones sin inicializador no
producen código (el TAC no las emite).

Solo usa la API del asignador (`regs.use`, `regs.def_`, `regs.into`); nunca
nombra registros de valores a mano.
"""

from __future__ import annotations

from asm.ir import FLOAT, Copy, Operand


class CoreSel:
    def sel_Copy(self, ins: Copy) -> None:
        dst, src = ins.dst, ins.src
        regs, asm = self.regs, self.a

        if src.is_const:
            if dst.is_float and src.ty.kind != "float":
                # una constante entera donde se espera float: se convierte aquí
                value = float(src.value or 0)
                src = Operand(repr(value), "const", FLOAT, value)
            rd = regs.def_(dst)
            regs.into(rd, src)  # li / la / l.s según el tipo
            return

        rs = regs.use(src)
        rd = regs.def_(dst)  # puede reutilizar `rs` si `src` ya murió
        if rd != rs:
            asm.ins(f"mov.s {rd}, {rs}" if dst.is_float else f"move  {rd}, {rs}")
