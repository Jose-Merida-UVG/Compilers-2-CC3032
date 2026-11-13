"""IR del Proyecto 3: el TAC convertido en objetos.

`tac_parser` lee el TAC y la tabla de símbolos y produce esto; los `sel_*.py`
solo trabajan con estas clases.

    Ty        tipo de un valor
    Operand   un valor (var, temp o const) con su Ty
    Instr     una línea del TAC; sus campos son Operands

    $t1 = b * 2   →   Binary(dst=$t1, a=b, op="*", b=2)

Se importa desde aquí: `from asm.ir import Binary, Operand`.
"""

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
