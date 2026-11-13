"""TrySel: `try`, `endtry` y `catch` (Tono).

    try L     rt_try_push con la dirección de L (el manejador)
    endtry    rt_try_pop
    catch e   e = el mensaje de la excepción (un string)

Un `throw` (runtime_exc.py) vuelve a L con `$sp` y `$fp` del `try`, y L empieza
un bloque con los registros vacíos: el manejador lee todo de memoria. Por eso, en
un programa que usa `try`, cada instrucción escribe su resultado a su casa al
terminar (`_dispatch` más abajo): si algo lanza a mitad del bloque, la memoria ya
está al día.
"""

from __future__ import annotations

from asm.ir import Catch, EndTry, Instr, Try


class TrySel:
    def sel_Try(self, ins: Try) -> None:
        self.regs.flush()  # lo anterior queda en memoria para el manejador
        self.a.ins(f"la    $a0, {ins.label}")
        self.a.ins("jal   rt_try_push")

    def sel_EndTry(self, ins: EndTry) -> None:
        self.a.ins("jal   rt_try_pop")

    def sel_Catch(self, ins: Catch) -> None:
        rd = self.regs.def_(ins.var)
        self.a.ins(f"lw    {rd}, exc_msg")

    # -- escritura inmediata -------------------------------------------------
    def _uses_try(self) -> bool:
        if not hasattr(self, "_has_try"):
            self._has_try = any(
                isinstance(i, Try) for fn in self.program.functions() for i in fn.body
            )
        return self._has_try

    def _dispatch(self, ins: Instr) -> None:
        super()._dispatch(ins)  # type: ignore[misc]  # el de BaseGen
        if self._uses_try():
            self.regs.flush()
