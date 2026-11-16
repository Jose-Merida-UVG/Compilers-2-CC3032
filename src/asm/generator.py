"""El driver de la generación de MIPS: convierte un programa en TAC a un `.s`.

Este archivo no sabe cómo se traduce ninguna instrucción en particular. Su trabajo
es la estructura que rodea a la traducción:

  * armar el esqueleto del programa (`main`, la zona de globales, el runtime);
  * recorrer cada función y partirla en bloques básicos;
  * decirle al asignador de registros cuándo empieza y termina cada bloque y
    cada instrucción (sin eso no puede calcular qué valores siguen vivos);
  * entregar cada instrucción al selector que sabe traducirla.

El flujo completo, de principio a fin:

    TAC (texto) ──parse_tac──▶ Program (objetos del IR, ver asm/ir/)
                                   │
                    AsmGenerator.run() recorre cada función:
                                   │
         por cada instrucción ──▶ _dispatch ──▶ sel_<Clase>  (sel_*.py)
                                                    │ pide registros a RegAlloc
                                                    ▼ y escribe MIPS con AsmEmitter
                               AsmResult (líneas crudas, sin mirilla)

Quién decide qué: este archivo decide *cuándo* se guarda todo a memoria (antes de
un salto, al cambiar de bloque); `regalloc.py` decide *en qué registro* vive cada
valor; `frames.py` decide *en qué dirección de la pila* vive su copia en memoria; y
los selectores deciden *qué instrucciones MIPS* salen. Por eso un selector nunca
nombra un registro para un valor: se lo pide al asignador.

La entrada pública es `generate_asm`. Se llama desde `compiler.analyze()` y solo
si el programa no tuvo ningún error léxico, sintáctico ni semántico.
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
    """Lo que devuelve `generate_asm`.

    `lines` es el MIPS tal como lo escribieron los selectores; la mirilla
    (`peephole.py`) se aplica después, fuera de este archivo, para poder mostrar
    el antes y el después en el IDE.
    """

    lines: list[str]
    activation: dict = field(default_factory=dict)  # marcos y árbol de llamadas
    regalloc_trace: list[dict] = field(default_factory=list)  # decisiones de getReg


class BaseGen:
    """La parte del generador que no depende de ninguna instrucción concreta.

    Guarda el estado que comparten todos los selectores y recorre el programa.
    Los selectores (`CoreSel`, `OpsSel`, ...) no heredan de esta clase: son
    mixins que dependen de que `AsmGenerator` la tenga en su lista de bases.
    Usan estos atributos, que se crean aquí:

        self.program  el `Program` completo (para consultar tipos de funciones)
        self.a        el `AsmEmitter`: donde se escribe el `.s`
        self.fr       el `FrameInfo` de la función que se está generando
        self.regs     el `RegAlloc` de esa función (uno nuevo por función)

    Va al final de la lista de bases de `AsmGenerator` a propósito: así un mixin
    puede redefinir un método de esta clase (`TrySel` redefine `_dispatch`).
    """

    def __init__(self, program: Program, asm: AsmEmitter, strict: bool = True) -> None:
        self.program = program
        self.a = asm
        # con strict=False una instrucción sin selector deja un "# TODO" en vez de
        # fallar; solo lo usan las pruebas que arman un generador incompleto
        self.strict = strict
        self.trace: list[dict] = []  # decisiones de getReg de todas las funciones
        self.frames: dict[str, FrameInfo] = {}  # los marcos, para activation.py
        self.fr: Optional[FrameInfo] = None
        self.regs: Optional[RegAlloc] = None

    def fn_label(self, tac_label: str) -> str:
        """Nombre MIPS de una función o método del TAC.

        Los métodos se llaman `Animal.hablar` en el TAC y un punto no es válido
        en una etiqueta de MIPS, por eso se pasa por `mangle_func`.
        """
        return mangle_func(tac_label)

    def run(self) -> None:
        """Escribe el programa completo en el emisor.

        El orden importa porque `.text` se ejecuta de arriba hacia abajo: lo
        primero es `main`, que prepara `$gp` y llama a la función `__main` (el
        código suelto del programa fuente, que el TAC ya agrupó en una función).
        Después van todas las funciones y métodos, y al final las rutinas del
        runtime (`print`, memoria, strings, excepciones) y las tablas de métodos
        de las clases, que no dependen del programa.
        """
        a = self.a
        a.data("        .align 2")
        a.data(f"__globals: .space {self.program.globals_size}")

        a.label("main")
        # los globales se direccionan como `N($gp)`, con los offsets que dejó
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
        """Genera el código de una función o método.

        Cada función se genera de forma independiente, con su propio marco y su
        propio asignador de registros: ningún registro cruza de una función a
        otra, así que no hay nada que arrastrar entre ellas.

        El cuerpo se parte en *bloques básicos* (tramos sin saltos adentro ni
        etiquetas en el medio). El asignador razona bloque por bloque: al
        entrar a uno no confía en que ningún registro tenga nada, y al salir
        deja todo lo importante guardado en memoria. Eso hace que dos bloques
        nunca se pasen valores por registros y por eso la lógica de los saltos
        es sencilla, a costa de algunos `sw`/`lw` de más en los bordes.

        Para cada instrucción el driver solo avisa al asignador qué instrucción
        viene (`begin_instr`) y cuándo terminó (`end_instr`, que libera los
        registros de los temporales que ya no se usan); el trabajo real ocurre en
        el selector.
        """
        a = self.a
        fr = FrameInfo(unit)
        self.fr = fr
        self.frames[unit.label] = fr
        self.regs = RegAlloc(a, fr.home)
        self.regs.trace = self.trace

        a.comment(f"función {unit.label}")
        fr.emit_prologue(a)

        blocks = split_blocks(unit.body)
        # los temporales que siguen vivos al salir de cada bloque no pueden darse
        # por muertos aunque el bloque ya no los use
        live_out = block_live_out(blocks)

        for blk, lo in zip(blocks, live_out):
            self.regs.start_block(blk, lo)
            for i, ins in enumerate(blk):
                self.regs.begin_instr(i)
                a.tac_comment(ins.line)
                if isinstance(ins, TERMINATORS):
                    # un salto o un return abandona el bloque: la memoria tiene
                    # que estar al día antes, pero los registros aún valen, así
                    # que la condición del salto se lee de ellos sin recargar
                    self.regs.flush()
                self._dispatch(ins)
                self.regs.end_instr(ins)
            if not isinstance(blk[-1], TERMINATORS):
                # el bloque termina porque sigue una etiqueta y se cae en ella
                self.regs.flush()

        fr.emit_epilogue(a)

    def _dispatch(self, ins: Instr) -> None:
        """Entrega una instrucción del IR al selector que sabe traducirla.

        El selector se busca por nombre: una `Binary` va a `sel_Binary`, una
        `Call` a `sel_Call`, y así. Agregar una instrucción nueva al IR es crear
        su clase y escribir el `sel_<Clase>` en el mixin que corresponda; este
        método no cambia.
        """
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
        # `ControlSel` define este mismo selector y gana por el orden de las
        # bases; esta copia solo cubre a un generador armado sin `ControlSel`
        self.a.label(ins.name)


class AsmGenerator(CoreSel, OpsSel, ControlSel, ArraySel, CallSel, ObjectSel, TrySel, BaseGen):
    """El generador completo: `BaseGen` más todos los selectores.

    No tiene cuerpo. Cada mixin aporta los métodos `sel_*` de un grupo de
    instrucciones y `BaseGen` aporta el estado y el recorrido; Python los junta
    en una sola clase, así que dentro de cualquier selector `self.regs`,
    `self.a` y `self.fr` son los mismos objetos.

        CoreSel     Copy                          (declaraciones y asignaciones)
        OpsSel      Unary, Binary, Print          (aritmética, lógica, print)
        ControlSel  Label, Goto, CondJump         (if, while, for, switch...)
        ArraySel    NewArray, Len, IndexLoad/Store
        CallSel     Call, Return                  (secuencia de llamada)
        ObjectSel   New, FieldLoad/Store, VTable*, CallVirt
        TrySel      Try, EndTry, Catch            (excepciones)
    """


def generate_asm(
    tac: list[str],
    symbol_table: dict,
    *,
    tac_comments: bool = True,
    strict: bool = True,
    generator_class: Optional[type] = None,
) -> AsmResult:
    """TAC y tabla de símbolos -> MIPS crudo.

    `symbol_table` es el JSON del Proyecto 2 (con tamaños, offsets y direcciones
    ya asignados): de ahí salen las casas en memoria y los tipos que el TAC no
    trae. Es la única información que se usa además del TAC; el generador nunca
    mira el árbol sintáctico.

    Si el parser tuvo que adivinar algo, falla en lugar de seguir: un tipo mal
    inferido produce un programa que compila pero imprime basura, y eso es peor
    que un error visible.

    `tac_comments` agrega `# TAC: ...` encima del código de cada instrucción.
    `strict` y `generator_class` existen para las pruebas del driver (permiten
    probarlo con selectores de mentira o con algunos selectores ausentes).
    """
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
