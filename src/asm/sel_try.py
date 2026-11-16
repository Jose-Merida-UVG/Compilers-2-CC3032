"""Selector de `try`, `endtry` y `catch`.

Un `throw` (runtime_exc.py) vuelve al `catch` con el `$sp` y `$fp` del `try` y
los registros vacíos. Por eso, en un programa con `try`, cada instrucción guarda
su resultado a memoria al terminar.
"""

from __future__ import annotations

from asm.ir import Catch, EndTry, Instr, Try


class TrySel:
    """Selector de excepciones: `try`, `endtry` y `catch`."""

    def sel_Try(self, ins: Try) -> None:
        """Registra el manejador."""
        self.regs.flush()  # Lo anterior queda en memoria para el manejador
        self.a.ins(f"la    $a0, {ins.label}")
        self.a.ins("jal   rt_try_push")

    def sel_EndTry(self, ins: EndTry) -> None:
        """Sale de la región protegida: desapila el manejador."""
        self.a.ins("jal   rt_try_pop")

    def sel_Catch(self, ins: Catch) -> None:
        """Entrada del manejador: la variable del `catch` recibe el mensaje."""
        rd = self.regs.def_(ins.var)
        self.a.ins(f"lw    {rd}, exc_msg")

    def _uses_try(self) -> bool:
        """¿El programa tiene algún `try`? Se calcula una vez y se recuerda."""
        if not hasattr(self, "_has_try"):
            self._has_try = any(
                isinstance(i, Try) for fn in self.program.functions() for i in fn.body
            )
        return self._has_try

    def _dispatch(self, ins: Instr) -> None:
        """Con `try`, guarda a memoria el resultado de cada instrucción (ver el docstring del módulo)."""
        super()._dispatch(ins)  # type: ignore[misc]  # el de BaseGen
        if self._uses_try():
            self.regs.flush()
