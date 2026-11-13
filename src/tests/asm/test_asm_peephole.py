"""Mirilla: cada regla por separado y que optimizar no cambie lo que imprime un programa."""

from __future__ import annotations

import glob
import os

import pytest
from antlr4 import InputStream

from asm.generator import generate_asm
from asm.peephole import optimize
from compiler import analyze
from support.minisim import Sim

HERE = os.path.dirname(os.path.abspath(__file__))


def test_redundant_move_is_removed():
    out, changes = optimize(["    move  $t0, $t0", "    move  $t0, $t1"])
    assert out == ["    move  $t0, $t1"]
    assert changes == {"move_redundante": 1}


def test_jump_to_the_next_label_is_removed_even_across_comments_and_labels():
    out, changes = optimize(["    j     L1", "    # TAC: x", "M:", "L1:", "    jr    $ra"])
    assert out == ["    # TAC: x", "M:", "L1:", "    jr    $ra"]
    assert changes == {"salto_a_la_siguiente": 1}


def test_jump_is_kept_when_an_instruction_sits_before_the_label():
    lines = ["    j     L1", "    li    $t0, 1", "L1:", "    jr    $ra"]
    assert optimize(lines) == (lines, {})


def test_load_right_after_store_of_the_same_register_and_address_is_removed():
    out, changes = optimize(["    sw    $t0, -4($fp)", "    # TAC: y", "    lw    $t0, -4($fp)"])
    assert out == ["    sw    $t0, -4($fp)", "    # TAC: y"]
    assert changes == {"carga_tras_guardar": 1}
    out, _ = optimize(["    swc1  $f4, 0($gp)", "    lwc1  $f4, 0($gp)"])
    assert out == ["    swc1  $f4, 0($gp)"]


def test_load_is_kept_when_a_label_separates_it_or_the_operands_differ():
    for lines in (
        ["    sw    $t0, 0($fp)", "L:", "    lw    $t0, 0($fp)"],  # alguien puede saltar al lw
        ["    sw    $t0, 0($fp)", "    lw    $t1, 0($fp)"],  # otro registro
        ["    sw    $t0, 0($fp)", "    lw    $t0, 4($fp)"],  # otra dirección
        ["    sb    $t0, 0($fp)", "    lb    $t0, 0($fp)"],  # lb extiende el signo: no es igual
    ):
        assert optimize(lines) == (lines, {})


VALID = sorted(glob.glob(os.path.join(HERE, "*", "valido_*.cps")))


@pytest.mark.parametrize("path", VALID, ids=[os.path.relpath(p, HERE) for p in VALID])
def test_optimized_programs_print_the_same(path):
    with open(path[:-4] + ".out", encoding="utf-8") as fh:
        expected = fh.read()
    with open(path, encoding="utf-8") as fh:
        result = analyze(InputStream(fh.read()))
    raw = generate_asm(result["tac"], result["symbol_table_json"]).lines
    optimized, _ = optimize(raw)
    assert len(optimized) <= len(raw)
    sim = Sim(optimized)
    assert sim.run() == expected
    assert sim.exit_code == 0
