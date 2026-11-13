"""IR tipado del Proyecto 3: el TAC (texto) convertido en objetos.

`tac_parser.parse_tac` produce esto; los selectores de instrucciones
(`sel_*.py`) trabajan únicamente con estas clases y nunca vuelven a leer
texto.

Cada instrucción guarda en `line` el texto TAC del que salió (se emite como
comentario en el `.s`) y expone `reads()` / `writes()`: los operandos que
lee y escribe, que el asignador de registros usa para calcular el siguiente
uso de cada valor."""

from __future__ import annotations

from asm.ir.types import (
    Ty,
    INT,
    FLOAT,
    BOOL,
    STR,
    NULL,
    VOID,
    VTABLE,
    UNKNOWN,
    array_of,
    obj_of,
)
from asm.ir.operands import (
    Operand,
)
from asm.ir.base import (
    Instr,
)
from asm.ir.control import (
    Label,
    Goto,
    CondJump,
    Return,
    TERMINATORS,
)
from asm.ir.values import (
    Copy,
    Unary,
    Binary,
    Print,
)
from asm.ir.arrays import (
    NewArray,
    Len,
    IndexLoad,
    IndexStore,
)
from asm.ir.objects import (
    FieldLoad,
    FieldStore,
    New,
    VTableLoad,
)
from asm.ir.calls import (
    Call,
    CallVirt,
)
from asm.ir.exceptions import (
    Try,
    EndTry,
    Catch,
)
from asm.ir.units import (
    FuncUnit,
    ClassUnit,
    Program,
)

__all__ = [
    "Ty",
    "INT",
    "FLOAT",
    "BOOL",
    "STR",
    "NULL",
    "VOID",
    "VTABLE",
    "UNKNOWN",
    "array_of",
    "obj_of",
    "Operand",
    "Instr",
    "Label",
    "Goto",
    "CondJump",
    "Return",
    "TERMINATORS",
    "Copy",
    "Unary",
    "Binary",
    "Print",
    "NewArray",
    "Len",
    "IndexLoad",
    "IndexStore",
    "FieldLoad",
    "FieldStore",
    "New",
    "VTableLoad",
    "Call",
    "CallVirt",
    "Try",
    "EndTry",
    "Catch",
    "FuncUnit",
    "ClassUnit",
    "Program",
]
