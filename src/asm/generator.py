"""Generador de MIPS: recorre el IR y despacha cada instrucción a su selector.

Entrada: el TAC (texto) y el JSON de la tabla de símbolos del Proyecto 2.
Salida: `AsmResult` con las líneas MIPS "crudas" (sin mirilla), los datos de
registros de activación y la traza de `getReg`. Contrato:
docs/proyecto3/01-contrato.md.

El driver es dueño de la estructura (prólogo, epílogo, bloques básicos,
`flush`/`invalidate` en los límites de bloque); los selectores de cada
instrucción viven en mixins `sel_*.py`, uno por dueño, y se importan **con
respaldo**: si el archivo aún no existe se usa una clase vacía. Así nadie tiene
que crear archivos ajenos.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from typing import Callable, Optional

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
from asm.tac_parser import parse_tac


def _mixin(module: str, name: str) -> type:
    """Clase `name` de `module`, o una clase vacía si el módulo aún no existe."""
    try:
        return getattr(importlib.import_module(module), name)
    except ModuleNotFoundError as exc:
        if exc.name != module:  # un fallo DENTRO del módulo no se esconde
            raise
        return type(name, (), {})


def _soft_func(module: str, name: str) -> Optional[Callable]:
    try:
        return getattr(importlib.import_module(module), name)
    except (ModuleNotFoundError, AttributeError) as exc:
        if isinstance(exc, ModuleNotFoundError) and exc.name != module:
            raise
        return None


CoreSel = _mixin("asm.sel_core", "CoreSel")  # Cami
OpsSel = _mixin("asm.sel_ops", "OpsSel")  # Nes
ControlSel = _mixin("asm.sel_control", "ControlSel")  # Nes
ArraySel = _mixin("asm.sel_arrays", "ArraySel")  # Nes
CallSel = _mixin("asm.sel_calls", "CallSel")  # Nes
ObjectSel = _mixin("asm.sel_objects", "ObjectSel")  # Tono
TrySel = _mixin("asm.sel_try", "TrySel")  # Tono

# Quién debe implementar cada instrucción (para el mensaje de error)
OWNERS = {
    "Copy": "Cami", "Unary": "Nes", "Binary": "Nes", "Print": "Nes",
    "CondJump": "Nes", "Goto": "Nes", "NewArray": "Nes", "Len": "Nes",
    "IndexLoad": "Nes", "IndexStore": "Nes", "Call": "Nes", "Return": "Nes",
    "New": "Tono", "FieldLoad": "Tono", "FieldStore": "Tono",
    "VTableLoad": "Tono", "CallVirt": "Tono", "Try": "Tono",
    "EndTry": "Tono", "Catch": "Tono",
}


@dataclass
class AsmResult:
    lines: list[str]  # MIPS crudo (sin mirilla)
    activation: dict = field(default_factory=dict)
    regalloc_trace: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


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

        # runtime y datos de otros dueños (si ya existen)
        emit_runtime = _soft_func("asm.runtime", "emit_runtime")
        if emit_runtime:
            emit_runtime(a)
        emit_exc = _soft_func("asm.runtime_exc", "emit_exc_runtime")
        if emit_exc:
            emit_exc(a)
        emit_vt = _soft_func("asm.sel_objects", "emit_vtables")
        if emit_vt:
            emit_vt(a, self.program.class_units())

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
                owner = OWNERS.get(name, "?")
                raise NotImplementedError(
                    f"falta el selector sel_{name} (dueño: {owner}); "
                    f"instrucción TAC: {ins.line!r}"
                )
            self.a.comment(f"TODO sel_{name}")
            return
        sel(ins)

    # -- selector por defecto: una etiqueta solo se escribe -----------------
    def sel_Label(self, ins: Label) -> None:
        self.a.label(ins.name)


class AsmGenerator(CoreSel, OpsSel, ControlSel, ArraySel, CallSel, ObjectSel, TrySel, BaseGen):
    """Compone los selectores de todos los dueños."""


def generate_asm(
    tac: list[str],
    symbol_table: dict,
    *,
    tac_comments: bool = True,
    strict: bool = True,
    generator_class: Optional[type] = None,
) -> AsmResult:
    """TAC + tabla de símbolos -> MIPS crudo.

    `strict=False` salta con un comentario las instrucciones cuyo selector aún
    no existe (útil mientras el equipo termina sus archivos).
    `generator_class` permite a las pruebas inyectar selectores propios.
    """
    program = parse_tac(tac, symbol_table)
    asm = AsmEmitter(tac_comments=tac_comments)
    gen = (generator_class or AsmGenerator)(program, asm, strict=strict)
    gen.run()

    activation: dict = {}
    build = _soft_func("asm.activation", "build_activation")
    if build:
        activation = build(program, gen.frames)
    return AsmResult(
        lines=asm.lines(),
        activation=activation,
        regalloc_trace=gen.trace,
        warnings=program.warnings,
    )
