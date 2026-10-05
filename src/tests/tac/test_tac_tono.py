"""Batería de TAC de Tono: funciones, recursividad, clases, herencia y
tabla de símbolos, más casos puntuales de clases.

Usa `compile_tac` directo (no `analyze()`).

- `valido_X.cps`  -> sin errores y con TAC. `compile_tac` además falla si queda
  un temporal vivo (fuga) y el Emitter lo comprueba al cerrar cada función.
- `invalido_X.cps` -> al menos un error y ningún TAC (R8).
"""
import glob
import os

import pytest

from conftest import compile_tac

_HERE = os.path.dirname(os.path.abspath(__file__))
_AREAS = ("funciones", "recursividad", "clases", "herencia", "tabla_simbolos")


def _cases(prefix: str) -> list[str]:
    return sorted(
        path
        for area in _AREAS
        for path in glob.glob(os.path.join(_HERE, area, f"{prefix}_*.cps"))
    )


def _id(path: str) -> str:
    return os.path.relpath(path, _HERE)


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


@pytest.mark.parametrize("path", _cases("valido"), ids=_id)
def test_valid_case_generates_tac(path):
    errors, tac = compile_tac(_read(path))
    assert errors == [], f"{_id(path)}: {errors}"
    assert tac, f"{_id(path)}: no se generó TAC"


@pytest.mark.parametrize("path", _cases("invalido"), ids=_id)
def test_invalid_case_reports_errors_and_no_tac(path):
    errors, tac = compile_tac(_read(path))
    assert errors != [], f"{_id(path)} debería reportar un error"
    assert tac is None, f"{_id(path)}: con errores no debe haber TAC"


def test_every_area_has_enough_cases():
    """≥3 válidos y ≥2 inválidos por área ."""
    for area in _AREAS:
        valid = glob.glob(os.path.join(_HERE, area, "valido_*.cps"))
        invalid = glob.glob(os.path.join(_HERE, area, "invalido_*.cps"))
        assert len(valid) >= 3, f"{area}: solo {len(valid)} válidos"
        assert len(invalid) >= 2, f"{area}: solo {len(invalid)} inválidos"


def test_property_assignment_as_expression_yields_the_assigned_value():
    """`let x = (o.a = 5);` guarda en el campo y `x` recibe el valor asignado."""
    errors, tac = compile_tac(
        "class Caja { var a: integer = 0; var b: integer = 0; }\n"
        "let o = new Caja();\n"
        "let x = (o.a = 5);\n"
        "let y = o.b = 7;\n"
        "print(x + y);\n"
    )
    assert errors == []
    main = tac[tac.index("func __main():"):]
    assert main.index("    o.a = 5") < main.index("    x = 5")
    assert main.index("    o.b = 7") < main.index("    y = 7")


def test_method_call_is_dispatched_through_the_vtable():
    """`a.hablar()` con `a: Animal` que guarda un `Perro` llama a la entrada del
    slot 0 de la tabla del objeto, no a `Animal.hablar`."""
    errors, tac = compile_tac(
        "class Animal { function hablar(): string { return \"...\"; } }\n"
        "class Perro : Animal { function hablar(): string { return \"guau\"; } }\n"
        "let a: Animal = new Perro();\n"
        "print(a.hablar());\n"
    )
    assert errors == []
    assert "    vtable Animal.hablar" in tac and "    vtable Perro.hablar" in tac
    main = tac[tac.index("func __main():"):]
    call = main.index("    $t1 = vtable a")
    assert main[call:call + 4] == [
        "    $t1 = vtable a",
        "    $t1 = $t1[0]",
        "    param a",
        "    $t1 = callvirt $t1, 1",
    ]
    assert not any("call Animal.hablar" in line or "call Perro.hablar" in line for line in main)


def test_this_method_call_inside_a_class_is_virtual_too():
    """`this.hablar()` desde el padre debe llegar al método sobrescrito."""
    errors, tac = compile_tac(
        "class Animal {\n"
        "  function hablar(): string { return \"...\"; }\n"
        "  function presentar(): string { return hablar(); }\n"
        "}\n"
        "class Perro : Animal { function hablar(): string { return \"guau\"; } }\n"
        "let p = new Perro();\n"
        "print(p.presentar());\n"
    )
    assert errors == []
    body = tac[tac.index("func Animal.presentar(this):"):]
    body = body[:body.index("endfunc")]
    assert body == [
        "func Animal.presentar(this):",
        "    $t1 = vtable this",
        "    $t1 = $t1[0]",
        "    param this",
        "    $t1 = callvirt $t1, 1",
        "    return $t1",
    ]


def test_constructor_and_init_fields_stay_static():
    errors, tac = compile_tac(
        "class A { var x: integer = 1; function constructor(v: integer) { this.x = v; } }\n"
        "class B : A { }\n"
        "let b = new B(2);\n"
    )
    assert errors == []
    main = tac[tac.index("func __main():"):]
    assert "    call B.__init_fields, 1" in main
    assert "    call A.constructor, 2" in main
    assert not any("callvirt" in line for line in tac)
