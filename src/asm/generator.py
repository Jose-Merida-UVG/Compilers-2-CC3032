"""Generador de MIPS: recorre el IR y despacha cada instrucción a su selector.

Entrada: el TAC (texto) y el JSON de la tabla de símbolos del Proyecto 2.
Salida: `AsmResult` con las líneas MIPS "crudas" (sin mirilla), los datos de
registros de activación y la traza de `getReg`.

El driver se encarga de la estructura (prólogo, epílogo, bloques básicos,
`flush`/`invalidate` en los límites de bloque); la traducción de cada
instrucción vive en los mixins `sel_*.py`, que `AsmGenerator` junta.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from asm.activation import build_activation
from asm.emitter import AsmEmitter, mangle_func
from asm.frames import FrameInfo
from asm.ir import (
    TERMINATORS,
    FuncUnit,
    Instr,
    Label,
    Program,
)
from asm.regalloc import RegAlloc, block_live_out, split_blocks
from asm.runtime import emit_runtime
from asm.runtime_exc import emit_exc_runtime
from asm.sel_arrays import ArraySel
from asm.sel_calls import CallSel
from asm.sel_control import ControlSel
from asm.sel_core import CoreSel
from asm.sel_objects import ObjectSel, emit_vtables
from asm.sel_ops import OpsSel
from asm.sel_try import TrySel
from asm.tac_parser import parse_tac


@dataclass
class AsmResult:
    lines: list[str]  # MIPS crudo (sin mirilla)
    activation: dict = field(default_factory=dict)
    regalloc_trace: list[dict] = field(default_factory=list)


class BaseGen:
    """Estructura del programa; se lista al final de las bases para que los
    mixins puedan sobreescribir cualquier `sel_*`."""

    def __init__(self, program: Program, asm: AsmEmitter, strict: bool = True) -> None:
        self.program = program
        self.a = asm
        self.strict = strict
        self.trace: list[dict] = []
        self.frames: dict[str, FrameInfo] = {}
        self.fr: Optional[FrameInfo] = None
        self.regs: Optional[RegAlloc] = None

    # -- utilidades para los selectores ----------------------------------
    def fn_label(self, tac_label: str) -> str:
        """Nombre MIPS seguro de una función o método del TAC."""
        return mangle_func(tac_label)

    # -- programa completo -------------------------------------------------
    def run(self) -> None:
        a = self.a
        a.data("        .align 2")
        a.data(f"__globals: .space {self.program.globals_size}")

        a.label("main")
        a.ins("la    $gp, __globals")  # los offsets `gp+N` de la tabla de símbolos valen
        a.ins(f"jal   {mangle_func('__main')}")
        a.ins("li    $v0, 10")
        a.ins("syscall")

        for unit in self.program.functions():
            self._gen_function(unit)

        # rutinas del runtime y tablas de métodos, después de todas las funciones
        emit_runtime(a)
        emit_exc_runtime(a)
        emit_vtables(a, self.program.class_units())

    def _gen_function(self, unit: FuncUnit) -> None:
        a = self.a
        fr = FrameInfo(unit)
        self.fr = fr
        self.frames[unit.label] = fr
        self.regs = RegAlloc(a, fr.home)
        self.regs.trace = self.trace

        a.comment(f"función {unit.label}")
        fr.emit_prologue(a)

        blocks = split_blocks(unit.body)
        live_out = block_live_out(blocks)
        for blk, lo in zip(blocks, live_out):
            self.regs.start_block(blk, lo)  # registros vacíos al entrar a un bloque
            for i, ins in enumerate(blk):
                self.regs.begin_instr(i)
                a.tac_comment(ins.line)
                if isinstance(ins, TERMINATORS):
                    self.regs.flush()  # la memoria queda al día antes de saltar
                self._dispatch(ins)
                self.regs.end_instr(ins)
            if not isinstance(blk[-1], TERMINATORS):
                self.regs.flush()  # cae al siguiente bloque

        fr.emit_epilogue(a)

    def _dispatch(self, ins: Instr) -> None:
        name = type(ins).__name__
        sel = getattr(self, "sel_" + name, None)
        if sel is None:
            if self.strict:
                raise NotImplementedError(
                    f"falta el selector sel_{name}; instrucción TAC: {ins.line!r}"
                )
            self.a.comment(f"TODO sel_{name}")
            return
        sel(ins)

    # -- selector por defecto: una etiqueta solo se escribe -----------------
    def sel_Label(self, ins: Label) -> None:
        self.a.label(ins.name)


class AsmGenerator(CoreSel, OpsSel, ControlSel, ArraySel, CallSel, ObjectSel, TrySel, BaseGen):
    """Junta los selectores de todas las instrucciones."""


def generate_asm(
    tac: list[str],
    symbol_table: dict,
    *,
    tac_comments: bool = True,
    strict: bool = True,
    generator_class: Optional[type] = None,
) -> AsmResult:
    """TAC + tabla de símbolos -> MIPS crudo.

    `strict=False` salta con un comentario las instrucciones sin selector
    (lo usan las pruebas que arman un generador parcial).
    `generator_class` permite a las pruebas inyectar selectores propios.
    """
    program = parse_tac(tac, symbol_table)
    if program.warnings:
        # el parser tuvo que adivinar un tipo o una dirección: mejor fallar que
        # generar código que quizá imprime basura
        raise ValueError("inferencia incompleta: " + "; ".join(program.warnings))
    asm = AsmEmitter(tac_comments=tac_comments)
    gen = (generator_class or AsmGenerator)(program, asm, strict=strict)
    gen.run()

    return AsmResult(
        lines=asm.lines(),
        activation=build_activation(program, gen.frames),
        regalloc_trace=gen.trace,
    )
