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
    lines = ["    j     L1", "M:", "    li    $t0, 1", "L1:", "    jr    $ra"]
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


def test_store_right_after_load_of_the_same_register_and_address_is_removed():
    out, changes = optimize(["    lw    $t0, 8($gp)", "    # TAC: y", "    sw    $t0, 8($gp)"])
    assert out == ["    lw    $t0, 8($gp)", "    # TAC: y"]
    assert changes == {"guardar_tras_cargar": 1}


def test_store_is_kept_when_the_load_changes_its_own_address_or_a_label_separates_them():
    for lines in (
        ["    lw    $t0, 0($t0)", "    sw    $t0, 0($t0)"],  # la base es el registro cargado
        ["    lw    $t0, 0($fp)", "L:", "    sw    $t0, 0($fp)"],
        ["    lw    $t0, 0($fp)", "    sw    $t0, 4($fp)"],
    ):
        assert optimize(lines) == (lines, {})


def test_arithmetic_identities_are_removed():
    lines = ["    addiu $t0, $t0, 0", "    addu  $t1, $t1, $zero",
             "    sll   $t2, $t2, 0", "    ori   $t3, $t3, 0", "    addiu $t0, $t1, 0"]
    out, changes = optimize(lines)
    assert out == ["    addiu $t0, $t1, 0"]  # destino distinto: no es una identidad
    assert changes == {"identidad_aritmetica": 4}


def test_move_back_and_forth_drops_the_second_move():
    out, changes = optimize(["    move  $t0, $t1", "    move  $t1, $t0"])
    assert out == ["    move  $t0, $t1"]
    assert changes == {"move_ida_y_vuelta": 1}
    lines = ["    move  $t0, $t1", "    move  $t2, $t0"]
    assert optimize(lines) == (lines, {})


def test_branch_over_a_jump_is_inverted():
    out, changes = optimize(["    beq   $t0, $zero, L1", "    j     L2", "L1:", "    jr    $ra"])
    assert out == ["    bne   $t0, $zero, L2", "L1:", "    jr    $ra"]
    assert changes == {"salto_sobre_salto": 1}
    out, _ = optimize(["    bne   $t0, $t1, L1", "    j     L2", "M:", "L1:", "    jr    $ra"])
    assert out[0] == "    beq   $t0, $t1, L2"


def test_branch_is_kept_when_it_does_not_target_the_label_after_the_jump():
    lines = ["    beq   $t0, $zero, L3", "    j     L2", "L1:", "    jr    $ra"]
    assert optimize(lines) == (lines, {})


def test_code_after_an_unconditional_jump_is_dead_until_the_next_label():
    out, changes = optimize(["    j     L9", "    li    $t0, 1", "    # TAC: x",
                             "    addu  $t1, $t0, $t0", "L1:", "    jr    $ra"])
    assert out == ["    j     L9", "    # TAC: x", "L1:", "    jr    $ra"]
    assert changes == {"codigo_muerto": 2}


def test_dead_code_stops_at_a_label_or_directive():
    lines = ["    jr    $ra", "L1:", "    li    $t0, 1", "    j     L1", "    .data"]
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


def test_jump_to_a_jump_goes_straight_to_the_final_target():
    lines = ["    j     L1", "    li    $t0, 1", "L1:", "    j     L2", "    li    $t1, 2", "L2:", "    jr    $ra"]
    out, changes = optimize(lines)
    assert changes["salto_a_salto"] >= 1  # `j L1` pasa a `j L2` (y luego el resto queda muerto)
    assert "    j     L1" not in out
    out, _ = optimize(["    beq   $t0, $t1, L1", "    li    $t2, 1", "L1:", "    j     L9", "L9:", "    jr    $ra"])
    assert out[0] == "    beq   $t0, $t1, L9"


def test_jump_threading_ignores_a_label_that_does_not_lead_to_a_jump():
    lines = ["    j     L1", "L0:", "    li    $t0, 1", "L1:", "    li    $t1, 2", "    jr    $ra"]
    assert optimize(lines)[0][0] == "    j     L1"


def test_consecutive_stack_adjustments_are_fused():
    out, changes = optimize(["    addiu $sp, $sp, 4", "    # TAC: x", "    addiu $sp, $sp, -8", "    sw    $t0, 0($sp)"])
    assert out == ["    # TAC: x", "    addiu $sp, $sp, -4", "    sw    $t0, 0($sp)"] or \
        out == ["    addiu $sp, $sp, -4", "    # TAC: x", "    sw    $t0, 0($sp)"]
    assert changes == {"fusion_ajustes_sp": 1}
    out, _ = optimize(["    addiu $sp, $sp, 4", "    addiu $sp, $sp, -4", "    jr    $ra"])
    assert out == ["    jr    $ra"]


def test_stack_adjustments_are_not_fused_across_a_label_or_another_instruction():
    for lines in (
        ["    addiu $sp, $sp, 4", "L:", "    addiu $sp, $sp, -4"],
        ["    addiu $sp, $sp, 4", "    sw    $t0, 0($sp)", "    addiu $sp, $sp, -4"],
    ):
        assert optimize(lines) == (lines, {})
