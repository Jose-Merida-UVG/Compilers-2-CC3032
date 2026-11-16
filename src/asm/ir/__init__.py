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

from asm.ir.arrays import IndexLoad, IndexStore, Len, NewArray
from asm.ir.base import Instr, non_const
from asm.ir.calls import Call, CallVirt
from asm.ir.control import TERMINATORS, CondJump, Goto, Label, Return
from asm.ir.exceptions import Catch, EndTry, Try
from asm.ir.objects import FieldLoad, FieldStore, New, VTableLoad, VTableSlotLoad
from asm.ir.operands import Operand
from asm.ir.types import (  # noqa: F401  (se reexportan)
    BOOL,
    FLOAT,
    INT,
    NULL,
    STR,
    UNKNOWN,
    VOID,
    VTABLE,
    Ty,
    array_of,
    obj_of,
)
from asm.ir.units import ClassUnit, FuncUnit, Program
from asm.ir.values import Binary, Copy, Print, Unary
