"""TAC (texto) -> IR tipado.

Entrada: las líneas del TAC que genera el Proyecto 2 y el JSON de la tabla de
símbolos (`symbol_table_json`). Salida: un `Program` (ver ir.py). **Nada de
esto mira el árbol sintáctico ni el checker**: el ensamblador se genera solo
a partir del TAC y de la tabla de símbolos.

El TAC no trae tipos para los temporales (`$t1 = a + b` no dice si es entero o
float), así que aquí se infieren con un recorrido lineal por unidad
(docs/proyecto3/01-contrato.md §3.1):

  * variables y parámetros: el `type` de su símbolo;
  * constantes: por su forma;
  * `x = y op z`: float si algún operando lo es, `str` si `+` con strings,
    `bool` si es una comparación, `int` en otro caso;
  * `call f`: tipo de retorno de `f` (la tabla de símbolos trae `"(a, b) -> r"`);
  * `x = y.f`: tipo del campo `f` en la clase de `y`;
  * `x = y[i]`: elemento de `y`;
  * `callvirt t`: se resuelve `t` por `vtable obj` + `[slot]` (tipo estático).
"""

from __future__ import annotations

import re
from typing import Optional

from asm.ir import (
    BOOL,
    FLOAT,
    INT,
    NULL,
    STR,
    UNKNOWN,
    VOID,
    VTABLE,
    Binary,
    Call,
    CallVirt,
    Catch,
    ClassUnit,
    CondJump,
    Copy,
    EndTry,
    FieldLoad,
    FieldStore,
    FuncUnit,
    Goto,
    IndexLoad,
    IndexStore,
    Instr,
    Label,
    Len,
    New,
    NewArray,
    Operand,
    Print,
    Program,
    Return,
    Try,
    Ty,
    Unary,
    VTableLoad,
    array_of,
    obj_of,
)

MAIN = "__main"
WORD = 4
SAVED = 8

# ── Patrones del TAC ────────────────────────────────────────────────────
_ID = r"[A-Za-z_][A-Za-z0-9_]*"
_TEMP = r"\$t\d+"
_NUM = r"-?\d+(?:\.\d+)?"
_STR = r"\x00S\d+\x00"
_ATOM = rf"(?:{_TEMP}|{_STR}|{_NUM}|{_ID})"
_REF = rf"(?:{_TEMP}|{_ID})"  # algo que puede tener campos o índice
_REL = r"(?:==|!=|<=|>=|<|>)"
_OP = r"(?:==|!=|<=|>=|<|>|\+|-|\*|/|%)"

_RE_FUNC = re.compile(rf"^func\s+(\S+?)\((.*)\):$")
_RE_CLASS = re.compile(rf"^class\s+({_ID})(?:\s*:\s*({_ID}))?\s*:$")
_RE_LABEL = re.compile(r"^([A-Za-z_][\w]*):$")
_RE_GOTO = re.compile(r"^goto\s+(\S+)$")
_RE_IF_REL = re.compile(rf"^(if|ifFalse)\s+({_ATOM})\s+({_REL})\s+({_ATOM})\s+goto\s+(\S+)$")
_RE_IF = re.compile(rf"^(if|ifFalse)\s+({_ATOM})\s+goto\s+(\S+)$")
_RE_PARAM = re.compile(rf"^param\s+({_ATOM})$")
_RE_CALL = re.compile(rf"^(?:({_REF})\s*=\s*)?call\s+(\S+),\s*(\d+)$")
_RE_CALLV = re.compile(rf"^(?:({_REF})\s*=\s*)?callvirt\s+({_ATOM}),\s*(\d+)$")
_RE_RETURN = re.compile(rf"^return(?:\s+({_ATOM}))?$")
_RE_PRINT = re.compile(rf"^print\s+({_ATOM})$")
_RE_TRY = re.compile(r"^try\s+(\S+)$")
_RE_CATCH = re.compile(rf"^catch\s+({_ID})$")
_RE_STORE_IDX = re.compile(rf"^({_REF})\[({_ATOM})\]\s*=\s*({_ATOM})$")
_RE_STORE_FLD = re.compile(rf"^({_REF})\.({_ID})\s*=\s*({_ATOM})$")
_RE_ASSIGN = re.compile(rf"^({_REF})\s*=\s*(.+)$")

_RE_NEWARRAY = re.compile(rf"^newarray\s+({_ATOM})$")
_RE_LEN = re.compile(rf"^len\s+({_ATOM})$")
_RE_NEW = re.compile(rf"^new\s+({_ID})$")
_RE_VTABLE = re.compile(rf"^vtable\s+({_ATOM})$")
_RE_ITOF = re.compile(rf"^itof\s+({_ATOM})$")
_RE_UNARY = re.compile(rf"^(-|!)\s+({_ATOM})$")
_RE_IDX = re.compile(rf"^({_REF})\[({_ATOM})\]$")
_RE_FLD = re.compile(rf"^({_REF})\.({_ID})$")
_RE_BIN = re.compile(rf"^({_ATOM})\s+({_OP})\s+({_ATOM})$")
_RE_ATOM = re.compile(rf"^{_ATOM}$")

_RE_STRLIT = re.compile(r'"(?:[^"\\]|\\.)*"')
_RE_TEMPNUM = re.compile(r"^\$t(\d+)$")
_RE_NUMBER = re.compile(rf"^{_NUM}$")
_RE_FUNCTYPE = re.compile(r"^\((.*)\)\s*->\s*(.+)$")

_REL_OPS = {"==", "!=", "<", "<=", ">", ">="}


# ── Tipos a partir del texto de la tabla de símbolos ─────────────────────
def ty_from_str(text: Optional[str]) -> Ty:
    """`"integer"`, `"float[]"`, `"Animal"`, … -> Ty."""
    if text is None:
        return UNKNOWN
    text = text.strip()
    if text.endswith("[]"):
        return array_of(ty_from_str(text[:-2]))
    simple = {
        "integer": INT,
        "float": FLOAT,
        "boolean": BOOL,
        "string": STR,
        "void": VOID,
        "null": NULL,
        "unknown": UNKNOWN,
    }
    if text in simple:
        return simple[text]
    if text.startswith("(") or text == "":
        return UNKNOWN
    return obj_of(text)


def _split_params(text: str) -> list[str]:
    depth, cur, out = 0, "", []
    for ch in text:
        if ch in "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


# ── Información sacada de la tabla de símbolos ───────────────────────────
class _SymbolInfo:
    def __init__(self, table: dict):
        self.root = table or {}
        self.func_scopes: dict[str, dict] = {}
        self.classes: dict[str, dict] = {}
        self.func_types: dict[str, tuple[list[Ty], Ty]] = {}
        self.global_symbols: dict[str, dict] = {}
        self._walk(self.root, None)
        if self.root.get("frame"):
            self.func_scopes[self.root["frame"]["label"]] = self.root
        self.global_symbols = self._collect_data(self.root)

    # recorrido completo para indexar funciones, clases y tipos de funciones
    def _walk(self, scope: dict, enclosing_class: Optional[str]) -> None:
        for sym in scope.get("symbols", []):
            if sym.get("kind") == "FUNCTION" and sym.get("label"):
                m = _RE_FUNCTYPE.match(sym.get("type") or "")
                if m:
                    params = [ty_from_str(p) for p in _split_params(m.group(1))]
                    self.func_types[sym["label"]] = (params, ty_from_str(m.group(2)))
        kind = scope.get("kind")
        if kind == "CLASS" and scope.get("owner"):
            name = scope["owner"]
            fields = {
                s["name"]: s.get("type")
                for s in scope.get("symbols", [])
                if s.get("kind") in ("VARIABLE", "CONSTANT")
            }
            self.classes[name] = {
                "layout": scope.get("layout", {}),
                "fields": fields,
                "parent": (scope.get("layout") or {}).get("parent"),
            }
        if kind == "FUNCTION" and scope.get("frame"):
            self.func_scopes[scope["frame"]["label"]] = scope
        for child in scope.get("children", []):
            self._walk(child, name if kind == "CLASS" else enclosing_class)

    # símbolos de datos de una unidad: propios + los de sus bloques
    def _collect_data(self, scope: dict) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for sym in scope.get("symbols", []):
            if sym.get("kind") in ("VARIABLE", "CONSTANT", "PARAMETER"):
                out[sym.get("tac_name") or sym["name"]] = sym
        for child in scope.get("children", []):
            if child.get("kind") == "BLOCK":
                out.update(self._collect_data(child))
        return out

    def unit_symbols(self, label: str) -> dict[str, dict]:
        scope = self.func_scopes.get(label)
        local = self._collect_data(scope) if scope is not None else {}
        merged = dict(self.global_symbols)
        merged.update(local)
        return merged

    def field(self, cls: Optional[str], name: str) -> Optional[dict]:
        """Entrada del layout (name, offset, size) del campo `name` de `cls`."""
        info = self.classes.get(cls or "")
        if info is None:
            return None
        for f in info["layout"].get("fields", []):
            if f["name"] == name:
                return f
        return None

    def field_type(self, cls: Optional[str], name: str) -> Ty:
        seen = set()
        while cls and cls not in seen:
            seen.add(cls)
            info = self.classes.get(cls)
            if info is None:
                break
            if name in info["fields"]:
                return ty_from_str(info["fields"][name])
            cls = info["parent"]
        return UNKNOWN

    def find_field_owner(self, name: str) -> Optional[str]:
        for cname in self.classes:
            if self.field(cname, name):
                return cname
        return None


# ── Parser de una unidad (función o método) ──────────────────────────────
class _UnitParser:
    def __init__(self, label: str, params: list[str], info: _SymbolInfo, warnings: list):
        self.label = label
        self.params = params
        self.info = info
        self.warnings = warnings
        self.symbols = info.unit_symbols(label)
        self.owner = label.split(".")[0] if "." in label else None
        self.env: dict[str, Ty] = {}
        self.vt_class: dict[str, str] = {}  # temporal -> clase de la vtable que contiene
        self.method_of: dict[str, str] = {}  # temporal -> etiqueta del método (slot)
        self.pending: list[Operand] = []
        self.max_temp = 0
        self.strings: list[str] = []
        self.param_types: dict[str, Ty] = {}
        for name in params:
            if name == "this":
                self.env[name] = obj_of(self.owner) if self.owner else UNKNOWN
            else:
                sym = self.symbols.get(name)
                self.env[name] = ty_from_str(sym["type"]) if sym else UNKNOWN
            self.param_types[name] = self.env[name]

    # -- operandos -------------------------------------------------------
    def warn(self, msg: str) -> None:
        self.warnings.append(f"{self.label}: {msg}")

    def operand(self, text: str) -> Operand:
        text = text.strip()
        if text in ("true", "false"):
            return Operand(text, "const", BOOL, text == "true", 4)
        if text == "null":
            return Operand(text, "const", NULL, None, 4)
        if text.startswith("\x00S"):
            lit = self.strings[int(text[2:-1])]
            return Operand(lit, "const", STR, lit[1:-1], 4)
        if _RE_NUMBER.match(text):
            if "." in text:
                return Operand(text, "const", FLOAT, float(text), 4)
            return Operand(text, "const", INT, int(text), 4)
        m = _RE_TEMPNUM.match(text)
        if m:
            self.max_temp = max(self.max_temp, int(m.group(1)))
            return Operand(text, "temp", self.env.get(text, UNKNOWN), None, 4)
        sym = self.symbols.get(text)
        size = int(sym["size"]) if sym and sym.get("size") else 4
        if text in self.params:
            size = 4  # los parámetros siempre ocupan una palabra
        ty = self.env.get(text)
        if ty is None:
            ty = ty_from_str(sym["type"]) if sym else UNKNOWN
            self.env[text] = ty
        return Operand(text, "var", ty, None, size)

    def dest(self, text: str, ty: Ty) -> Operand:
        """Operando destino con el tipo ya calculado."""
        text = text.strip()
        m = _RE_TEMPNUM.match(text)
        if m:
            self.max_temp = max(self.max_temp, int(m.group(1)))
            if ty.kind == "unknown":
                ty = INT
                self.warn(f"tipo desconocido para {text}; se asume int")
            self.env[text] = ty
            return Operand(text, "temp", ty, None, 4)
        op = self.operand(text)
        known = op.ty
        if known.kind == "unknown":
            op.ty = ty if ty.kind != "unknown" else INT
            self.env[text] = op.ty
        return op

    # -- inferencia ------------------------------------------------------
    @staticmethod
    def bin_type(a: Ty, op: str, b: Ty) -> Ty:
        if op in _REL_OPS:
            return BOOL
        if a.kind == "float" or b.kind == "float":
            return FLOAT
        if op == "+" and (a.kind == "str" or b.kind == "str"):
            return STR
        return INT

    def class_of(self, op: Operand) -> Optional[str]:
        return op.ty.cls if op.ty.kind == "obj" else None

    # -- una línea -------------------------------------------------------
    def parse_line(self, raw: str) -> Optional[Instr]:
        line = raw.strip()
        if not line:
            return None
        # los strings se sustituyen por marcadores para no confundir operadores
        self.strings = []

        def hide(m: re.Match) -> str:
            self.strings.append(m.group(0))
            return f"\x00S{len(self.strings) - 1}\x00"

        text = _RE_STRLIT.sub(hide, line)
        ins = self._dispatch(text)
        if ins is None:
            raise ValueError(f"{self.label}: no entiendo la instrucción TAC: {line!r}")
        ins.line = line
        return ins

    def _dispatch(self, t: str) -> Optional[Instr]:  # noqa: C901 (es una tabla de formas)
        m = _RE_LABEL.match(t)
        if m:
            return Label(m.group(1))
        m = _RE_GOTO.match(t)
        if m:
            return Goto(m.group(1))
        m = _RE_IF_REL.match(t)
        if m:
            return CondJump(m.group(1), self.operand(m.group(2)), m.group(3),
                            self.operand(m.group(4)), m.group(5))
        m = _RE_IF.match(t)
        if m:
            return CondJump(m.group(1), self.operand(m.group(2)), None, None, m.group(3))
        m = _RE_PARAM.match(t)
        if m:
            self.pending.append(self.operand(m.group(1)))
            return _Param()
        m = _RE_CALL.match(t)
        if m:
            return self._call(m)
        m = _RE_CALLV.match(t)
        if m:
            return self._callvirt(m)
        m = _RE_RETURN.match(t)
        if m:
            return Return(self.operand(m.group(1)) if m.group(1) else None)
        m = _RE_PRINT.match(t)
        if m:
            return Print(self.operand(m.group(1)))
        m = _RE_TRY.match(t)
        if m:
            return Try(m.group(1))
        if t == "endtry":
            return EndTry()
        m = _RE_CATCH.match(t)
        if m:
            return Catch(self.dest(m.group(1), STR))
        m = _RE_STORE_IDX.match(t)
        if m:
            return IndexStore(self.operand(m.group(1)), self.operand(m.group(2)),
                              self.operand(m.group(3)))
        m = _RE_STORE_FLD.match(t)
        if m:
            return self._field_store(m)
        m = _RE_ASSIGN.match(t)
        if m:
            return self._assign(m.group(1), m.group(2).strip())
        return None

    # -- llamadas --------------------------------------------------------
    def _take_args(self, n: int) -> list[Operand]:
        if len(self.pending) != n:
            self.warn(f"call con {n} argumentos pero {len(self.pending)} param pendientes")
        args = self.pending[-n:] if n else []
        self.pending = []
        return args

    def _ret_type(self, label: Optional[str]) -> Ty:
        if label and label in self.info.func_types:
            return self.info.func_types[label][1]
        return UNKNOWN

    def _call(self, m: re.Match) -> Instr:
        callee, n = m.group(2), int(m.group(3))
        args = self._take_args(n)
        dst = self.dest(m.group(1), self._ret_type(callee)) if m.group(1) else None
        return Call(dst, callee, args)

    def _callvirt(self, m: re.Match) -> Instr:
        target = self.operand(m.group(2))
        n = int(m.group(3))
        args = self._take_args(n)
        label = self.method_of.get(target.text)
        dst = self.dest(m.group(1), self._ret_type(label)) if m.group(1) else None
        return CallVirt(dst, target, args, static_target=label)

    # -- campos ----------------------------------------------------------
    def _field_info(self, obj: Operand, name: str) -> tuple[Optional[str], int, int]:
        cls = self.class_of(obj)
        f = self.info.field(cls, name)
        if f is None:
            owner = self.info.find_field_owner(name)
            if owner is not None:
                self.warn(f"clase de {obj.text} desconocida; se usa {owner}.{name}")
                cls, f = owner, self.info.field(owner, name)
        if f is None:
            self.warn(f"campo {name} no encontrado en el layout")
            return cls, 0, 4
        return cls, int(f["offset"]), int(f.get("size", 4))

    def _field_store(self, m: re.Match) -> Instr:
        obj = self.operand(m.group(1))
        src = self.operand(m.group(3))
        cls, off, size = self._field_info(obj, m.group(2))
        return FieldStore(obj, m.group(2), src, offset=off, fsize=size)

    # -- asignaciones ----------------------------------------------------
    def _assign(self, dst_text: str, rest: str) -> Optional[Instr]:  # noqa: C901
        m = _RE_NEWARRAY.match(rest)
        if m:
            n = self.operand(m.group(1))
            return NewArray(self.dest(dst_text, array_of(None)), n)
        m = _RE_LEN.match(rest)
        if m:
            src = self.operand(m.group(1))
            return Len(self.dest(dst_text, INT), src)
        m = _RE_NEW.match(rest)
        if m:
            cls = m.group(1)
            layout = self.info.classes.get(cls, {}).get("layout", {})
            dst = self.dest(dst_text, obj_of(cls))
            return New(dst, cls, size=int(layout.get("size", WORD)))
        m = _RE_VTABLE.match(rest)
        if m:
            obj = self.operand(m.group(1))
            dst = self.dest(dst_text, VTABLE)
            dst.ty = VTABLE
            self.env[dst.text] = VTABLE
            cls = self.class_of(obj)
            if cls:
                self.vt_class[dst.text] = cls
            return VTableLoad(dst, obj)
        m = _RE_ITOF.match(rest)
        if m:
            src = self.operand(m.group(1))
            return Unary(self.dest(dst_text, FLOAT), "itof", src)
        m = _RE_UNARY.match(rest)
        if m:
            src = self.operand(m.group(2))
            ty = BOOL if m.group(1) == "!" else src.ty
            return Unary(self.dest(dst_text, ty), m.group(1), src)
        m = _RE_IDX.match(rest)
        if m:
            base = self.operand(m.group(1))
            idx = self.operand(m.group(2))
            if base.ty.kind == "vtable":
                return self._vtable_entry(dst_text, base, idx)
            elem = base.ty.elem if base.ty.kind == "array" and base.ty.elem else UNKNOWN
            return IndexLoad(self.dest(dst_text, elem), base, idx)
        m = _RE_FLD.match(rest)
        if m:
            obj = self.operand(m.group(1))
            cls, off, size = self._field_info(obj, m.group(2))
            ty = self.info.field_type(cls, m.group(2))
            return FieldLoad(self.dest(dst_text, ty), obj, m.group(2), offset=off, fsize=size)
        m = _RE_BIN.match(rest)
        if m:
            a, b = self.operand(m.group(1)), self.operand(m.group(3))
            ty = self.bin_type(a.ty, m.group(2), b.ty)
            return Binary(self.dest(dst_text, ty), a, m.group(2), b)
        if _RE_ATOM.match(rest):
            src = self.operand(rest)
            return Copy(self.dest(dst_text, src.ty), src)
        return None

    def _vtable_entry(self, dst_text: str, base: Operand, idx: Operand) -> Instr:
        """`$t = $v[k]` con `$v` una tabla de métodos: acceso crudo."""
        dst = self.dest(dst_text, INT)
        cls = self.vt_class.get(base.text)
        if cls and idx.is_const:
            vt = self.info.classes.get(cls, {}).get("layout", {}).get("vtable", [])
            for entry in vt:
                if entry.get("slot") == idx.value:
                    self.method_of[dst.text] = entry["label"]
        return IndexLoad(dst, base, idx)


class _Param(Instr):
    """Marcador interno: un `param` ya quedó en `pending`."""


# ── API ─────────────────────────────────────────────────────────────────
def parse_tac(lines: list[str], symbol_table: dict) -> Program:
    """Convierte el TAC en un `Program` tipado."""
    info = _SymbolInfo(symbol_table)
    warnings: list[str] = []
    units: list = []
    current_class: Optional[ClassUnit] = None
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].strip()
        i += 1
        if not line:
            continue
        m = _RE_CLASS.match(line)
        if m:
            name, parent = m.group(1), m.group(2)
            current_class = ClassUnit(
                name=name, parent=parent, vtable=[], funcs=[],
                layout=info.classes.get(name, {}).get("layout", {}),
            )
            units.append(current_class)
            continue
        if line == "endclass":
            current_class = None
            continue
        if line.startswith("vtable ") and current_class is not None:
            current_class.vtable = [s.strip() for s in line[len("vtable "):].split(",") if s.strip()]
            continue
        m = _RE_FUNC.match(line)
        if m:
            label = m.group(1)
            params = [p.strip() for p in m.group(2).split(",") if p.strip()]
            body_lines: list[str] = []
            while i < n and lines[i].strip() != "endfunc":
                body_lines.append(lines[i])
                i += 1
            i += 1  # endfunc
            unit = _parse_function(label, params, body_lines, info, warnings)
            if current_class is not None:
                unit.owner_class = current_class.name
                current_class.funcs.append(unit)
            else:
                units.append(unit)
            continue
        raise ValueError(f"línea TAC inesperada fuera de una unidad: {line!r}")

    classes = {name: c["layout"] for name, c in info.classes.items()}
    return Program(
        units=units,
        globals_size=_globals_size(info),
        classes=classes,
        func_types=dict(info.func_types),
        warnings=warnings,
    )


def _parse_function(label: str, params: list[str], body_lines: list[str],
                    info: _SymbolInfo, warnings: list) -> FuncUnit:
    up = _UnitParser(label, params, info, warnings)
    body: list[Instr] = []
    for raw in body_lines:
        ins = up.parse_line(raw)
        if ins is None or isinstance(ins, _Param):
            continue
        body.append(ins)
    scope = info.func_scopes.get(label)
    frame = dict((scope or {}).get("frame") or {})
    locals_size = _round(int(frame.get("locals_size", 0)))
    temps = max(int(frame.get("temps", 0)), up.max_temp)
    params_size = WORD * len(params)  # cada parámetro ocupa una palabra
    frame = {
        "label": label,
        "params_size": params_size,
        "locals_size": locals_size,
        "temps": temps,
        "temps_size": temps * WORD,
        "saved_size": SAVED,
        "total_size": params_size + locals_size + temps * WORD + SAVED,
    }
    return FuncUnit(
        label=label, params=params, body=body, frame=frame,
        symbols=up.symbols, param_types=up.param_types,
        owner_class=up.owner if "." in label else None,
    )


def _round(n: int) -> int:
    return (n + WORD - 1) // WORD * WORD


def _globals_size(info: _SymbolInfo) -> int:
    end = 0
    for sym in info.global_symbols.values():
        addr = sym.get("address") or ""
        if addr.startswith("gp+"):
            end = max(end, int(addr[3:]) + int(sym.get("size") or WORD))
    return max(WORD, _round(end))
