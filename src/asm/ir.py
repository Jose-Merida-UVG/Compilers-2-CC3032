"""IR tipado del Proyecto 3: el TAC (texto) convertido en objetos.

`tac_parser.parse_tac` produce esto; los selectores de instrucciones
(`sel_*.py`) trabajan únicamente con estas clases y nunca vuelven a leer
texto. Ver docs/proyecto3/01-contrato.md §3.

Cada instrucción guarda en `line` el texto TAC del que salió (se emite como
comentario en el `.s`) y expone `reads()` / `writes()`: los operandos que
lee y escribe, que el asignador de registros usa para calcular el siguiente
uso de cada valor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ── Tipos ───────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Ty:
    """Tipo estático de un valor del TAC.

    kind: 'int' 'float' 'bool' 'str' 'array' 'obj' 'vtable' 'null' 'void'
          'unknown'
    """

    kind: str
    elem: Optional["Ty"] = None  # solo para 'array'
    cls: Optional[str] = None  # solo para 'obj'

    @property
    def is_float(self) -> bool:
        return self.kind == "float"

    def __str__(self) -> str:  # pragma: no cover - solo depuración
        if self.kind == "array":
            return f"{self.elem}[]"
        if self.kind == "obj":
            return f"obj({self.cls})"
        return self.kind


INT = Ty("int")
FLOAT = Ty("float")
BOOL = Ty("bool")
STR = Ty("str")
NULL = Ty("null")
VOID = Ty("void")
VTABLE = Ty("vtable")
UNKNOWN = Ty("unknown")


def array_of(elem: Optional[Ty]) -> Ty:
    return Ty("array", elem=elem)


def obj_of(cls: str) -> Ty:
    return Ty("obj", cls=cls)


# ── Operandos ───────────────────────────────────────────────────────────
@dataclass
class Operand:
    """Un valor del TAC: variable, temporal o constante.

    text:  tal cual en el TAC ("x", "x_1", "$t3", "5", "2.5", '"hola"', "true")
    kind:  'var' | 'temp' | 'const'
    ty:    tipo estático
    value: para 'const': int | float | bool | str (sin comillas) | None (null)
    size:  bytes que ocupa en memoria (1 si es un boolean con casa de 1 byte)
    """

    text: str
    kind: str
    ty: Ty = UNKNOWN
    value: object = None
    size: int = 4

    @property
    def is_const(self) -> bool:
        return self.kind == "const"

    @property
    def is_temp(self) -> bool:
        return self.kind == "temp"

    @property
    def is_float(self) -> bool:
        return self.ty.kind == "float"

    @property
    def key(self) -> str:
        """Identidad del valor en el asignador de registros."""
        return self.text

    def __repr__(self) -> str:  # pragma: no cover - solo depuración
        return f"{self.text}:{self.ty}"


# ── Instrucciones ───────────────────────────────────────────────────────
class Instr:
    """Base de todas las instrucciones del IR."""

    line: str = ""

    def reads(self) -> list[Operand]:
        return []

    def writes(self) -> list[Operand]:
        return []

    def __repr__(self) -> str:  # pragma: no cover - solo depuración
        return self.line or type(self).__name__


def _vals(*ops: Optional[Operand]) -> list[Operand]:
    return [o for o in ops if o is not None and not o.is_const]


@dataclass(repr=False)
class Label(Instr):
    name: str
    line: str = ""


@dataclass(repr=False)
class Goto(Instr):
    label: str
    line: str = ""


@dataclass(repr=False)
class CondJump(Instr):
    """`if a goto L`, `ifFalse a goto L`, `if a REL b goto L`."""

    sense: str  # 'if' | 'ifFalse'
    a: Operand
    rel: Optional[str]  # None => se prueba `a` solo
    b: Optional[Operand]
    label: str
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.a, self.b)


@dataclass(repr=False)
class Copy(Instr):
    dst: Operand
    src: Operand
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.src)

    def writes(self) -> list[Operand]:
        return [self.dst]


@dataclass(repr=False)
class Unary(Instr):
    dst: Operand
    op: str  # '-' | '!' | 'itof'
    src: Operand
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.src)

    def writes(self) -> list[Operand]:
        return [self.dst]


@dataclass(repr=False)
class Binary(Instr):
    dst: Operand
    a: Operand
    op: str  # + - * / % == != < <= > >=
    b: Operand
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.a, self.b)

    def writes(self) -> list[Operand]:
        return [self.dst]


@dataclass(repr=False)
class NewArray(Instr):
    dst: Operand
    n: Operand
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.n)

    def writes(self) -> list[Operand]:
        return [self.dst]


@dataclass(repr=False)
class Len(Instr):
    dst: Operand
    src: Operand
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.src)

    def writes(self) -> list[Operand]:
        return [self.dst]


@dataclass(repr=False)
class IndexLoad(Instr):
    dst: Operand
    base: Operand
    idx: Operand
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.base, self.idx)

    def writes(self) -> list[Operand]:
        return [self.dst]


@dataclass(repr=False)
class IndexStore(Instr):
    base: Operand
    idx: Operand
    src: Operand
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.base, self.idx, self.src)


@dataclass(repr=False)
class FieldLoad(Instr):
    dst: Operand
    obj: Operand
    field: str
    offset: int = 0  # offset del campo según el layout de la clase estática
    fsize: int = 4  # tamaño del campo (1 si es boolean)
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.obj)

    def writes(self) -> list[Operand]:
        return [self.dst]


@dataclass(repr=False)
class FieldStore(Instr):
    obj: Operand
    field: str
    src: Operand
    offset: int = 0
    fsize: int = 4
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.obj, self.src)


@dataclass(repr=False)
class New(Instr):
    dst: Operand
    cls: str
    size: int = 4  # layout.size de la clase
    line: str = ""

    def writes(self) -> list[Operand]:
        return [self.dst]


@dataclass(repr=False)
class VTableLoad(Instr):
    dst: Operand
    obj: Operand
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.obj)

    def writes(self) -> list[Operand]:
        return [self.dst]


@dataclass(repr=False)
class Call(Instr):
    dst: Optional[Operand]
    callee: str  # etiqueta TAC ("fact", "Animal.hablar")
    args: list[Operand]  # ya agrupados; len(args) == n
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(*self.args)

    def writes(self) -> list[Operand]:
        return [self.dst] if self.dst is not None else []


@dataclass(repr=False)
class CallVirt(Instr):
    dst: Optional[Operand]
    target: Operand  # contiene la dirección del método
    args: list[Operand]
    static_target: Optional[str] = None  # etiqueta resuelta por el tipo estático
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.target, *self.args)

    def writes(self) -> list[Operand]:
        return [self.dst] if self.dst is not None else []


@dataclass(repr=False)
class Return(Instr):
    src: Optional[Operand]
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.src)


@dataclass(repr=False)
class Print(Instr):
    src: Operand
    line: str = ""

    def reads(self) -> list[Operand]:
        return _vals(self.src)


@dataclass(repr=False)
class Try(Instr):
    label: str
    line: str = ""


@dataclass(repr=False)
class EndTry(Instr):
    line: str = ""


@dataclass(repr=False)
class Catch(Instr):
    var: Operand
    line: str = ""

    def writes(self) -> list[Operand]:
        return [self.var]


TERMINATORS = (Goto, CondJump, Return)


# ── Unidades ────────────────────────────────────────────────────────────
@dataclass
class FuncUnit:
    """Una función o método.

    label:   etiqueta TAC ("fact", "Animal.hablar", "__main")
    params:  nombres de los parámetros en orden (incluye `this` en métodos)
    body:    instrucciones
    frame:   {"params_size","locals_size","temps","temps_size","saved_size",
              "total_size"} (temps ya incluye los temporales realmente usados)
    symbols: tac_name -> {"kind","type","address","size"} visibles en la
             unidad (los de la propia función primero, luego los globales)
    owner_class: nombre de la clase si es un método
    """

    label: str
    params: list[str]
    body: list[Instr]
    frame: dict
    symbols: dict = field(default_factory=dict)
    owner_class: Optional[str] = None
    param_types: dict = field(default_factory=dict)


@dataclass
class ClassUnit:
    name: str
    parent: Optional[str]
    vtable: list[str]  # etiquetas TAC de los métodos, por slot
    funcs: list[FuncUnit]
    layout: dict = field(default_factory=dict)


@dataclass
class Program:
    units: list  # FuncUnit | ClassUnit, en el orden del TAC
    globals_size: int = 4
    classes: dict = field(default_factory=dict)  # nombre -> layout JSON
    func_types: dict = field(default_factory=dict)  # etiqueta -> (params, ret)
    warnings: list = field(default_factory=list)

    def functions(self) -> list[FuncUnit]:
        """Todas las funciones y métodos, en orden de emisión."""
        out: list[FuncUnit] = []
        for unit in self.units:
            if isinstance(unit, ClassUnit):
                out.extend(unit.funcs)
            else:
                out.append(unit)
        return out

    def class_units(self) -> list[ClassUnit]:
        return [u for u in self.units if isinstance(u, ClassUnit)]
