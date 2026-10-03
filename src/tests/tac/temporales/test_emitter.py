"""Pruebas de reciclaje, unidades y formato del emisor TAC."""
from __future__ import annotations

import pytest

from tac.emitter import Emitter


def test_reuses_smallest_free_index():
    e = Emitter()
    e.begin_unit("func __main():")

    first = e.new_temp()
    second = e.new_temp()
    assert (first, second) == ("$t1", "$t2")

    # Liberamos en orden inverso para verificar el menor índice.
    e.free(second)
    e.free(first)
    e.free(first)

    assert e.new_temp() == "$t1"
    assert e.new_temp() == "$t2"
    assert e.live_temps() == 2

    e.free("$t1")
    e.free("$t2")
    e.end_unit("endfunc")
    assert e.max_temps("__main") == 2


def test_non_temporary_operands_are_ignored():
    e = Emitter()
    e.begin_unit("func __main():")
    temporary = e.new_temp()

    for operand in (None, "", "x", "42", '"hola"', "$t99", "$t1_extra"):
        e.free(operand)

    assert e.live_temps() == 1
    e.free(temporary)
    e.end_unit("endfunc")


def test_nested_units_preserve_outer_temporaries():
    e = Emitter()
    e.begin_unit("func outer():")
    outer_temp = e.new_temp()

    e.begin_unit("func inner():")
    assert e.live_temps() == 0
    assert e.new_temp() == "$t1"
    assert e.new_temp() == "$t2"
    e.free("$t1")
    e.free("$t2")
    e.end_unit("endfunc")

    assert e.live_temps() == 1
    assert e.new_temp() == "$t2"
    e.free(outer_temp)
    e.free("$t2")
    e.end_unit("endfunc")

    assert e.max_temps("outer") == 2
    assert e.max_temps("inner") == 2
    assert e.lines() == [
        "func outer():",
        "endfunc",
        "func inner():",
        "endfunc",
    ]


def test_labels_are_global_and_main_is_last():
    e = Emitter()
    e.begin_unit("func __main():")
    first_label = e.new_label()
    e.emit_label(first_label)
    e.emit("print 1")

    e.begin_unit("func helper():")
    second_label = e.new_label()
    e.emit_label(second_label)
    e.emit("return")
    e.end_unit("endfunc")

    e.end_unit("endfunc")

    assert (first_label, second_label) == ("L1", "L2")
    assert e.lines() == [
        "func helper():",
        "L2:",
        "    return",
        "endfunc",
        "func __main():",
        "L1:",
        "    print 1",
        "endfunc",
    ]


def test_class_keeps_methods_inside_its_markers():
    e = Emitter()
    e.begin_unit("func __main():")
    e.begin_unit("class Perro : Animal:")
    e.begin_unit("func Perro.hablar(this):")
    e.emit('print "guau"')
    e.end_unit("endfunc")
    e.end_unit("endclass")
    e.end_unit("endfunc")

    assert e.lines() == [
        "class Perro : Animal:",
        "func Perro.hablar(this):",
        '    print "guau"',
        "endfunc",
        "endclass",
        "func __main():",
        "endfunc",
    ]


def test_leaks_are_reported_before_closing_unit():
    e = Emitter()
    e.begin_unit("func f():")
    temporary = e.new_temp()

    with pytest.raises(RuntimeError, match=r"Fuga de temporales en f: \$t1"):
        e.end_unit("endfunc")

    assert e.live_temps() == 1
    e.free(temporary)
    e.end_unit("endfunc")
    assert e.live_temps() == 0


def test_incomplete_units_cannot_be_exported():
    e = Emitter()
    e.begin_unit("func f():")

    with pytest.raises(RuntimeError, match="sin cerrar"):
        e.lines()

    with pytest.raises(ValueError, match="Cierre incorrecto"):
        e.end_unit("endclass")

    e.end_unit("endfunc")
    assert e.lines() == ["func f():", "endfunc"]