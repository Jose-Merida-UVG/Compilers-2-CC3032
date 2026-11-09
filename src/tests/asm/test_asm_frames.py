"""Pruebas de los registros de activación (`asm.frames`): casas, prólogo,
epílogo y casillas. Ver docs/proyecto3/01-contrato.md §2."""

from __future__ import annotations

from antlr4 import InputStream

from asm.emitter import AsmEmitter
from asm.frames import FrameInfo
from asm.ir import Operand, INT
from asm.tac_parser import parse_tac
from compiler import analyze

SRC = """
let g: integer = 1;
function f(a: integer, b: boolean, c: integer): integer {
    let x: integer = a + c;
    let y: boolean = b;
    return x * (x + 1) * (c + 2);
}
print(f(g, true, 3));
"""


def _frames():
    r = analyze(InputStream(SRC))
    assert r["errors"] == []
    prog = parse_tac(r["tac"], r["symbol_table_json"])
    return {u.label: FrameInfo(u) for u in prog.functions()}


def _op(text, kind="var"):
    return Operand(text, kind, INT)


def test_parameters_are_one_word_each_even_for_boolean():
    f = _frames()["f"]
    assert f.home(_op("a")).mem() == "8($fp)"
    assert f.home(_op("b")).mem() == "12($fp)"  # el layout de P2 diría fp+9
    assert f.home(_op("c")).mem() == "16($fp)"
    assert f.home(_op("b")).size == 4


def test_locals_come_from_the_symbol_table_and_booleans_use_a_byte():
    f = _frames()["f"]
    hx, hy = f.home(_op("x")), f.home(_op("y"))
    assert hx.base == "fp" and hx.offset < 0 and hx.size == 4
    assert hy.base == "fp" and hy.size == 1


def test_temporaries_live_below_the_locals():
    f = _frames()["f"]
    assert f.temps >= 2
    t1, t2 = f.home(_op("$t1", "temp")), f.home(_op("$t2", "temp"))
    assert t1.offset == -(f.locals_size + 4)
    assert t2.offset == -(f.locals_size + 8)


def test_globals_use_gp():
    main = _frames()["__main"]
    h = main.home(_op("g"))
    assert (h.base, h.offset) == ("gp", 0)
    # una función también ve los globales
    assert _frames()["f"].home(_op("g")).base == "gp"


def test_prologue_and_epilogue_follow_the_contract():
    f = _frames()["f"]
    asm = AsmEmitter()
    f.emit_prologue(asm)
    f.emit_epilogue(asm)
    text = "\n".join(asm._text)
    assert text.index("f_f:") < text.index("sw    $ra, 4($sp)") < text.index("move  $fp, $sp")
    assert f"addiu $sp, $sp, -{f.locals_size + f.temps_size}" in text
    assert "f_f__ret:" in text and "jr    $ra" in text


def test_slots_are_ordered_from_high_to_low_addresses():
    f = _frames()["f"]
    slots = f.slots()
    offsets = [s["offset"] for s in slots]
    assert offsets == sorted(offsets, reverse=True)
    names = [s["name"] for s in slots]
    assert names[:3] == ["c", "b", "a"]  # el último argumento está en la dirección más alta
    assert names.index("$ra") == 3 and names.index("$fp") == 4
    kinds = {s["name"]: s["kind"] for s in slots}
    assert kinds["x"] == "local" and kinds["$t1"] == "temp" and kinds["a"] == "param"


def test_main_has_its_own_frame_with_no_locals():
    main = _frames()["__main"]
    assert main.locals_size == 0 and main.fn_label == "f___main"
