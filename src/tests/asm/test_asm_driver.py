"""Pruebas del driver (`asm.generator`) y de `CoreSel`.

Dos niveles:
  * estructura del `.s` (texto): `main`, `__globals`, prólogo/epílogo, comentarios TAC;
  * comportamiento: se ejecuta el `.s` en un intérprete mínimo (`support/minisim.py`,
    NO es MARS) usando selectores de prueba para las demás instrucciones. Así el
    núcleo (`getReg`, marcos, secuencia de llamada, recursión) queda cubierto
    aunque los selectores reales de Nes y Tono todavía no existan.
"""

from __future__ import annotations

import pytest
from antlr4 import InputStream

from asm.generator import AsmGenerator, generate_asm
from compiler import analyze
from support.minisim import Sim
from support.testsel import RUNTIME, MiniGen


def _analyze(src: str):
    r = analyze(InputStream(src))
    assert r["errors"] == [], r["errors"]
    return r


def _asm(src: str, **kw):
    r = _analyze(src)
    return generate_asm(r["tac"], r["symbol_table_json"], **kw)


def _run(src: str) -> str:
    """Compila y corre con los selectores de prueba en el intérprete mínimo."""
    res = _asm(src, generator_class=MiniGen)
    return Sim(res.lines + RUNTIME).run()


# ── estructura ──────────────────────────────────────────────────────────
def test_program_skeleton():
    res = _asm("let a: integer = 5;", strict=False)
    text = "\n".join(res.lines)
    assert text.index(".data") < text.index("__globals: .space") < text.index(".text")
    assert "la    $gp, __globals" in text  # los offsets `gp+N` valen
    assert "jal   f___main" in text and "li    $v0, 10" in text
    assert "f___main:" in text and "f___main__ret:" in text
    assert ".globl main" in text and "\nmain:" in text


def test_tac_lines_are_commented_and_can_be_turned_off():
    with_c = "\n".join(_asm("let a: integer = 5;", strict=False).lines)
    assert "# TAC: a = 5" in with_c
    without = "\n".join(_asm("let a: integer = 5;", strict=False, tac_comments=False).lines)
    assert "# TAC:" not in without


def test_missing_selector_names_its_owner():
    with pytest.raises(NotImplementedError) as exc:
        _asm("let a = [1, 2];")  # NewArray: lo implementa Nes (sel_arrays.py)
    assert "sel_NewArray" in str(exc.value) and "Nes" in str(exc.value)


def test_non_strict_mode_leaves_a_todo_comment():
    text = "\n".join(_asm("let a = [1, 2];", strict=False).lines)
    assert "# TODO sel_NewArray" in text


def test_data_section_deduplicates_strings_and_floats():
    text = "\n".join(_asm('let a: string = "hola"; let b: string = "hola"; '
                         "let f: float = 2.5; let g: float = 2.5;", strict=False).lines)
    assert text.count(".asciiz") == 1 and text.count(".float") == 1


def test_globals_area_matches_the_symbol_table():
    res = _asm("let a: integer = 1; let b: integer = 2; let c: integer = 3;", strict=False)
    assert any(l.startswith("__globals: .space 12") for l in res.lines)


def test_copy_selector_for_each_kind_of_constant():
    text = "\n".join(_asm('let i: integer = 7; let t: boolean = true; let n: string = "x"; '
                         "let f: float = 1.5; let z: integer = 0;", strict=False).lines)
    assert "li    $t0, 7" in text
    assert "li    $t1, 1" in text           # true
    assert "la    $t2, str_0" in text       # string
    assert "l.s   $f4, flt_0" in text       # float
    assert "li    $t3, 0" in text


def test_copy_between_variables_does_not_move_a_register_onto_itself():
    text = "\n".join(l.strip() for l in _asm("let a: integer = 1; let b = a;", strict=False).lines)
    assert "move  $t0, $t0" not in text and "move  $t1, $t0" in text


def test_only_the_driver_flushes_at_block_ends():
    # tras `a = 5` solo hay una escritura de `a` a su casa (al final del bloque)
    text = "\n".join(_asm("let a: integer = 5;", strict=False).lines)
    assert text.count("sw    $t0, 0($gp)") == 1


# ── comportamiento (intérprete mínimo) ──────────────────────────────────
def test_loops_functions_and_recursion_run_correctly():
    out = _run("""
function fact(n: integer): integer {
    if (n <= 1) { return 1; }
    return n * fact(n - 1);
}
function suma(a: integer, b: integer): integer { return a + b; }
let i: integer = 0;
let total: integer = 0;
while (i < 5) {
    total = total + i * 2;
    i = i + 1;
}
print(total);
print(fact(5));
print(suma(fact(3), suma(1, 2)));
let k: integer = 7;
if (k % 2 == 0) { print(0); } else { print(1); }
for (let j: integer = 0; j < 3; j = j + 1) { print(j); }
""")
    assert out.split() == ["20", "120", "9", "1", "0", "1", "2"]


def test_register_pressure_spills_and_still_computes_correctly():
    n = 14
    decl = "\n".join(f"let v{i}: integer = {i + 1};" for i in range(2 * n))
    expr = ""
    for i in reversed(range(n)):
        term = f"(v{2 * i}*v{2 * i + 1})"
        expr = term if not expr else f"({term}+{expr})"
    src = decl + f"\nlet r = {expr};\nprint(r);\n"
    res = _asm(src, generator_class=MiniGen)
    assert any(t["reason"] == "spill" for t in res.regalloc_trace)  # sí hubo spill
    assert Sim(res.lines + RUNTIME).run().strip() == str(sum((2 * i + 1) * (2 * i + 2) for i in range(n)))


def test_variables_survive_branches_and_loops_through_memory():
    out = _run("""
let acc: integer = 0;
let flag: boolean = false;
let i: integer = 0;
while (i < 10) {
    if (i % 3 == 0) { acc = acc + i; flag = true; }
    i = i + 1;
}
print(acc);
if (flag) { print(1); } else { print(0); }
""")
    assert out.split() == [str(0 + 3 + 6 + 9), "1"]


def test_a_value_computed_before_a_call_is_still_correct_after_it():
    out = _run("""
function id(x: integer): integer { return x; }
let a: integer = 10;
let b = a * 3;
let c = id(b + 1);
print(a + b + c);
""")
    assert out.split() == [str(10 + 30 + 31)]


def test_ternary_result_lives_across_blocks():
    out = _run("""
let x: integer = 4;
let y: integer = 9;
let m = x > y ? x : y;
print(m);
""")
    assert out.split() == ["9"]
