"""Driver: recorre el TAC función por función y arma el `.s`.

    TAC ──parse_tac──▶ Program ──run()──▶ por función, por bloque, por instrucción:
          _dispatch ──▶ sel_<Clase> ──▶ AsmEmitter ──▶ AsmResult

Este archivo decide cuándo se hace flush (antes de saltos y al cambiar de
bloque). `regalloc.py` decide el registro de cada valor, `frames.py` su casa
en memoria y los `sel_*.py` las instrucciones MIPS.

`generate_asm` es la entrada; `compiler.analyze()` la llama si no hubo errores.
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
    """Lo que devuelve `generate_asm`."""

    lines: list[str]
    activation: dict = field(default_factory=dict)  # Marcos y árbol de llamadas
    regalloc_trace: list[dict] = field(default_factory=list)  # Decisiones de getReg


class BaseGen:
    """Estado compartido por los selectores y recorrido del programa."""

    def __init__(self, program: Program, asm: AsmEmitter, strict: bool = True) -> None:
        self.program = program
        self.a = asm
        # Con strict=False una instrucción sin selector deja un "# TODO" en vez de
        # fallar; solo lo usan las pruebas que arman un generador incompleto
        self.strict = strict
        self.trace: list[dict] = []  # Decisiones de getReg de todas las funciones
        self.frames: dict[str, FrameInfo] = {}  # Los marcos, para activation.py
        self.fr: Optional[FrameInfo] = None
        self.regs: Optional[RegAlloc] = None

    def fn_label(self, tac_label: str) -> str:
        """Nombre MIPS de una función o método del TAC."""
        return mangle_func(tac_label)

    def run(self) -> None:
        """Escribe el programa completo en el emisor."""
        a = self.a
        a.data("        .align 2")
        a.data(f"__globals: .space {self.program.globals_size}")

        a.label("main")
        # Los globales se direccionan como `N($gp)`, con los offsets que dejó
        # `semantic/layout.py` en la tabla de símbolos; aquí se fija la base
        a.ins("la    $gp, __globals")
        a.ins(f"jal   {mangle_func('__main')}")
        a.ins("li    $v0, 10")
        a.ins("syscall")

        for unit in self.program.functions():
            self._gen_function(unit)

        emit_runtime(a)
        emit_exc_runtime(a)
        emit_vtables(a, self.program.class_units())

    def _gen_function(self, unit: FuncUnit) -> None:
        """Genera el código de una función o método."""
        a = self.a
        fr = FrameInfo(unit)
        self.fr = fr
        self.frames[unit.label] = fr
        self.regs = RegAlloc(a, fr.home)
        self.regs.trace = self.trace

        a.comment(f"función {unit.label}")
        fr.emit_prologue(a)

        blocks = split_blocks(unit.body)
        # Los temporales que siguen vivos al salir de cada bloque no pueden darse
        # por muertos aunque el bloque ya no los use
        live_out = block_live_out(blocks)

        for blk, lo in zip(blocks, live_out):
            self.regs.start_block(blk, lo)
            for i, ins in enumerate(blk):
                self.regs.begin_instr(i)
                a.tac_comment(ins.line)
                if isinstance(ins, TERMINATORS):
                    # Un salto o un return abandona el bloque: la memoria tiene
                    # que estar al día antes, pero los registros aún valen, así
                    # que la condición del salto se lee de ellos sin recargar
                    self.regs.flush()
                self._dispatch(ins)
                self.regs.end_instr(ins)
            if not isinstance(blk[-1], TERMINATORS):
                # El bloque termina porque sigue una etiqueta y se cae en ella
                self.regs.flush()

        fr.emit_epilogue(a)

    def _dispatch(self, ins: Instr) -> None:
        """Entrega una instrucción del IR al selector que sabe traducirla."""
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

    def sel_Label(self, ins: Label) -> None:
        # Copia mínima para las pruebas que arman un generador sin `ControlSel`;
        # en `AsmGenerator` gana la de `ControlSel` por el orden de las bases
        self.a.label(ins.name)


class AsmGenerator(CoreSel, OpsSel, ControlSel, ArraySel, CallSel, ObjectSel, TrySel, BaseGen):
    """El generador completo."""


def generate_asm(
    tac: list[str],
    symbol_table: dict,
    *,
    tac_comments: bool = True,
    strict: bool = True,
    generator_class: Optional[type] = None,
) -> AsmResult:
    """TAC y tabla de símbolos -> MIPS crudo."""
    program = parse_tac(tac, symbol_table)
    if program.warnings:
        raise ValueError("inferencia incompleta: " + "; ".join(program.warnings))
    asm = AsmEmitter(tac_comments=tac_comments)
    gen = (generator_class or AsmGenerator)(program, asm, strict=strict)
    gen.run()

    return AsmResult(
        lines=asm.lines(),
        activation=build_activation(program, gen.frames),
        regalloc_trace=gen.trace,
    )
