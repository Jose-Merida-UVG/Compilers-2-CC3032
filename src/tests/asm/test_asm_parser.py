"""Pruebas del parser de TAC (`asm.tac_parser`): agrupación de `param`/`call`,
inferencia de tipos de temporales, clases/vtables y marcos.

No usan simulador. Ver docs/proyecto3/01-contrato.md §3.
"""

from __future__ import annotations

from antlr4 import InputStream

from asm.ir import (
    Binary, Call, CallVirt, ClassUnit, Copy, FieldLoad, FieldStore, IndexLoad,
    New, NewArray, Print, Return, Unary, VTableLoad,
)
from asm.tac_parser import parse_tac, ty_from_str
from compiler import analyze


def _program(src: str):
    r = analyze(InputStream(src))
    assert r["errors"] == [], r["errors"]
    return parse_tac(r["tac"], r["symbol_table_json"]), r


def _func(prog, label):
    return next(f for f in prog.functions() if f.label == label)


def _body(prog, label):
    return _func(prog, label).body


def test_ty_from_str():
    assert ty_from_str("integer").kind == "int"
    assert ty_from_str("float[]").elem.kind == "float"
    assert ty_from_str("Animal").cls == "Animal"
    assert ty_from_str("(integer) -> string").kind == "unknown"


def test_param_and_call_are_grouped_in_order():
    prog, _ = _program(
        "function f(a: integer, b: integer): integer { return a - b; }\n"
        "print(f(7, 2));"
    )
    call = next(i for i in _body(prog, "__main") if isinstance(i, Call))
    assert call.callee == "f"
    assert [a.text for a in call.args] == ["7", "2"]
    assert call.dst.ty.kind == "int"
    assert not any(type(i).__name__ == "_Param" for i in _body(prog, "__main"))


def test_float_and_string_inference_of_temporaries():
    prog, _ = _program(
        'let i: integer = 3; let f: float = 2.5; let a = i + f;'
        'let s: string = "x"; let t = s + "y"; let c = i < 4;'
    )
    binaries = [i for i in _body(prog, "__main") if isinstance(i, Binary)]
    by_op = {b.op: b for b in binaries}
    assert by_op["+"].dst.ty.kind in ("float", "str")
    kinds = {b.dst.ty.kind for b in binaries}
    assert {"float", "str", "bool"} <= kinds
    itof = next(i for i in _body(prog, "__main") if isinstance(i, Unary) and i.op == "itof")
    assert itof.dst.ty.kind == "float"


def test_call_result_takes_the_functions_return_type():
    prog, _ = _program(
        "function half(x: float): float { return x / 2.0; }\n"
        "let y = half(5.0); print(y);"
    )
    main = _body(prog, "__main")
    call = next(i for i in main if isinstance(i, Call))
    assert call.dst.ty.kind == "float"
    assert next(i for i in main if isinstance(i, Print)).src.ty.kind == "float"


def test_array_element_type_and_newarray():
    prog, _ = _program("let a = [1.5, 2.5]; let x = a[0]; print(x);")
    main = _body(prog, "__main")
    assert any(isinstance(i, NewArray) for i in main)
    load = next(i for i in main if isinstance(i, IndexLoad))
    assert load.dst.ty.kind == "float"


def test_boolean_parameters_take_a_full_word():
    prog, _ = _program(
        "function f(a: boolean, b: boolean, c: integer): integer { return c; }\n"
        "print(f(true, false, 3));"
    )
    f = _func(prog, "f")
    assert f.frame["params_size"] == 12  # 4 bytes por parámetro, aunque el layout diga 1
    assert all(op.size == 4 for op in [i for i in f.body if isinstance(i, Return)][0].reads())


CLASSES = """
class Animal {
    let nombre: string = "x";
    let patas: integer = 4;
    function constructor(n: string) { this.nombre = n; }
    function hablar(): string { return "..."; }
}
class Perro : Animal {
    let raza: float = 1.5;
    function hablar(): string { return "guau"; }
}
let p: Animal = new Perro("rex");
print(p.hablar());
print(p.patas);
"""


def test_classes_vtables_and_static_virtual_target():
    prog, _ = _program(CLASSES)
    classes = {c.name: c for c in prog.units if isinstance(c, ClassUnit)}
    assert classes["Perro"].parent == "Animal"
    assert classes["Perro"].vtable == ["Perro.hablar"]
    assert classes["Animal"].vtable == ["Animal.hablar"]
    main = _body(prog, "__main")
    new = next(i for i in main if isinstance(i, New))
    assert new.cls == "Perro" and new.size == 16
    assert any(isinstance(i, VTableLoad) for i in main)
    cv = next(i for i in main if isinstance(i, CallVirt))
    assert cv.static_target == "Animal.hablar"  # tipo estático de `p` es Animal
    assert cv.dst.ty.kind == "str"


def test_field_offsets_and_types_come_from_the_layout():
    prog, _ = _program(CLASSES)
    ctor = _body(prog, "Animal.constructor")
    store = next(i for i in ctor if isinstance(i, FieldStore))
    assert (store.field, store.offset) == ("nombre", 4)
    main = _body(prog, "__main")
    load = next(i for i in main if isinstance(i, FieldLoad))
    assert (load.field, load.offset) == ("patas", 8)
    assert load.dst.ty.kind == "int"
    init = _body(prog, "Perro.__init_fields")
    raza = next(i for i in init if isinstance(i, FieldStore) and i.field == "raza")
    assert raza.offset == 12 and raza.src.ty.kind == "float"


def test_methods_get_this_and_a_frame_even_without_a_scope():
    prog, _ = _program(CLASSES)
    hablar = _func(prog, "Animal.hablar")
    assert hablar.params == ["this"]
    assert hablar.frame["params_size"] == 4
    init = _func(prog, "Animal.__init_fields")  # sintetizado: no tiene ámbito propio
    assert init.params == ["this"]
    assert init.frame["total_size"] >= 12


def test_frame_temps_cover_the_highest_temporary_used():
    prog, _ = _program("let a: integer = 1; let r = (a + 1) * (a + 2) * (a + 3);")
    main = _func(prog, "__main")
    assert main.frame["temps"] >= 2
    assert main.frame["temps_size"] == 4 * main.frame["temps"]


def test_globals_size_is_word_aligned():
    prog, _ = _program("let a: integer = 1; let b: boolean = true; let c: integer = 2;")
    assert prog.globals_size % 4 == 0 and prog.globals_size >= 9


def test_copy_of_constants_keeps_value_and_type():
    prog, _ = _program('let s: string = "hola"; let n = null; let t = true; let f = 2.5;')
    copies = [i for i in _body(prog, "__main") if isinstance(i, Copy)]
    consts = {c.src.text: c.src for c in copies}
    assert consts['"hola"'].value == "hola" and consts['"hola"'].ty.kind == "str"
    assert consts["true"].value is True
    assert consts["2.5"].value == 2.5
