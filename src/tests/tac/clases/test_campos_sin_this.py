"""Un campo de la propia clase usado sin `this.` dentro de un método: el
checker lo resuelve por ámbito y el TAC debe leerlo y escribirlo en el objeto.
"""
from conftest import compile_tac


def method(source: str, label: str) -> list[str]:
    errors, tac = compile_tac(source)
    assert errors == []
    start = tac.index(next(l for l in tac if l.startswith(f"func {label}(")))
    return [l.strip() for l in tac[start + 1 : tac.index("endfunc", start)]]


def test_bare_field_write_goes_to_this():
    body = method("class C { var s: integer = 0; function a(m: integer) { s = m; } }", "C.a")
    assert body == ["this.s = m", "return"]


def test_bare_field_read_and_write_in_one_statement():
    body = method("class C { var s: integer = 0; function a(m: integer) { s = s + m; } }", "C.a")
    assert body == ["$t1 = this.s", "$t1 = $t1 + m", "this.s = $t1", "return"]


def test_local_with_the_same_name_hides_the_field():
    body = method(
        "class C { var s: integer = 0; function a(m: integer) { let s: integer = 1; s = m; } }",
        "C.a",
    )
    assert body == ["s = 1", "s = m", "return"]


def test_bare_field_assignment_used_as_an_expression_returns_the_value():
    body = method(
        "class C { var s: integer = 0; function a(m: integer): integer { return s = m; } }", "C.a"
    )
    assert body == ["this.s = m", "return m"]


def test_integer_assigned_to_a_float_field_is_promoted():
    body = method("class C { var f: float = 0.0; function a() { f = 2; } }", "C.a")
    assert body == ["this.f = 2.0", "return"]


def test_bare_field_write_in_constructor_and_nested_block():
    source = (
        "class C { var s: integer = 0;"
        "  function constructor(x: integer) { s = x; }"
        "  function a(m: integer) { if (m > 0) { s = m; } } }"
    )
    assert method(source, "C.constructor") == ["this.s = x", "return"]
    assert "this.s = m" in method(source, "C.a")


def test_plain_variable_assignment_is_unchanged():
    errors, tac = compile_tac("let x: integer = 1; x = 2; function f() { let y: integer = 1; y = 3; }")
    assert errors == []
    assert "    x = 2" in tac and "    y = 3" in tac
