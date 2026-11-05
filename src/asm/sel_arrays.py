"""ArraySel: arreglos con verificación de rango (Nes).

Formato (contrato §7): `[ longitud n ][ e0 ][ e1 ] ... [ e(n-1) ]`, 4 bytes por
elemento sin importar el tipo. Acceso a `base[idx]`:

    lw    len, 0(base)
    sltu  len, idx, len                # idx < len, SIN signo: un negativo también falla
    beq   len, $zero, rt_throw_index
    sll   t, idx, 2 ; addu t, t, base
    lw    dst, 4(t)

Un operando de tipo `vtable` (`x = vtable obj` del despacho dinámico) NO lleva
cabecera ni verificación: el índice es el número de slot y el acceso es
`lw dst, 4*slot(base)`.

Todos los cálculos auxiliares usan `regs.scratch()`; el destino se pide al
final (`def_` puede reutilizar el registro de un fuente que ya murió).
"""

from __future__ import annotations

from asm.ir import IndexLoad, IndexStore, Len, NewArray
from asm.sel_ops import as_float, as_float_operand


class ArraySel:
    def sel_NewArray(self, ins: NewArray) -> None:
        regs, asm = self.regs, self.a
        regs.into("$a0", ins.n)
        asm.ins("jal   rt_new_array")  # preserva los registros del asignador
        rd = regs.def_(ins.dst)
        asm.ins(f"move  {rd}, $v0")

    def sel_Len(self, ins: Len) -> None:
        regs, asm = self.regs, self.a
        rs = regs.use(ins.src)
        rd = regs.def_(ins.dst)
        asm.ins(f"lw    {rd}, 0({rs})")

    # -- lectura ---------------------------------------------------------------
    def sel_IndexLoad(self, ins: IndexLoad) -> None:
        regs, asm = self.regs, self.a
        rb = regs.use(ins.base)

        if ins.base.ty.kind == "vtable":  # acceso crudo a la tabla de métodos
            if not (ins.idx.is_const and isinstance(ins.idx.value, int)):
                raise NotImplementedError(f"vtable con índice no constante: {ins.line!r}")
            rd = regs.def_(ins.dst)
            asm.ins(f"lw    {rd}, {4 * ins.idx.value}({rb})")
            return

        offset, base_reg = self._element_address(ins.base, rb, ins.idx)
        if offset is None:  # índice constante negativo: siempre falla
            return
        rd = regs.def_(ins.dst)
        load = "lwc1 " if ins.dst.is_float else "lw   "
        asm.ins(f"{load} {rd}, {offset}({base_reg})")

    # -- escritura ---------------------------------------------------------------
    def sel_IndexStore(self, ins: IndexStore) -> None:
        regs, asm = self.regs, self.a
        rb = regs.use(ins.base)
        elem = ins.base.ty.elem
        to_float = ins.src.is_float or (elem is not None and elem.is_float)

        if to_float:
            if ins.src.is_const and ins.src.ty.kind != "float":
                rs = regs.use(as_float_operand(ins.src))
            else:
                rs = as_float(self, ins.src)
        else:
            rs = regs.use(ins.src)

        offset, base_reg = self._element_address(ins.base, rb, ins.idx)
        if offset is None:
            return
        store = "swc1 " if to_float else "sw   "
        asm.ins(f"{store} {rs}, {offset}({base_reg})")

    def _bounds_check(self, ri: str, length: str) -> None:
        """Salta a `rt_throw_index` si `ri` no está en [0, length). Compara sin
        signo (un índice negativo se ve como un número enorme) y usa solo
        instrucciones reales de MIPS; `length` se reutiliza como resultado."""
        self.a.ins(f"sltu  {length}, {ri}, {length}")
        self.a.ins(f"beq   {length}, $zero, rt_throw_index")

    # -- dirección del elemento ---------------------------------------------------
    def _element_address(self, base, rb: str, idx):
        """Verifica el rango y devuelve (desplazamiento, registro base) del
        elemento. Con índice constante no hace falta calcular la dirección."""
        regs, asm = self.regs, self.a

        if idx.is_const:
            k = int(idx.value or 0)
            if k < 0:  # fuera de rango en compilación
                asm.ins("j     rt_throw_index")
                return None, None
            length = regs.scratch()
            asm.ins(f"lw    {length}, 0({rb})")
            ri = regs.use(idx)  # $zero si k == 0, si no un registro con k
            self._bounds_check(ri, length)
            return 4 + 4 * k, rb

        ri = regs.use(idx)
        length = regs.scratch()
        addr = regs.scratch()
        asm.ins(f"lw    {length}, 0({rb})")
        self._bounds_check(ri, length)
        asm.ins(f"sll   {addr}, {ri}, 2")
        asm.ins(f"addu  {addr}, {addr}, {rb}")
        return 4, addr
