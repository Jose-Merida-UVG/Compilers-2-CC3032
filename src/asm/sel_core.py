"""Selector de asignaciones: `let x = y;`, `x = 5;`, `const K = "hola";`.

Llegan como `Copy`. Una declaración sin valor no genera código.
"""

from __future__ import annotations

from asm.ir import FLOAT, Copy, Operand


class CoreSel:
    """Selector del núcleo del lenguaje."""

    def sel_Copy(self, ins: Copy) -> None:
        """`x = y` o `x = constante`."""
        dst, src = ins.dst, ins.src
        regs, asm = self.regs, self.a

        if src.is_const:
            if dst.is_float and src.ty.kind != "float":
                # Una constante entera donde se espera float: se convierte aquí
                value = float(src.value or 0)
                src = Operand(repr(value), "const", FLOAT, value)
            rd = regs.def_(dst)
            regs.into(rd, src)
            return

        rs = regs.use(src)
        rd = regs.def_(dst)  # Puede reutilizar `rs` si `src` ya murió
        if rd != rs:
            asm.ins(f"mov.s {rd}, {rs}" if dst.is_float else f"move  {rd}, {rs}")
