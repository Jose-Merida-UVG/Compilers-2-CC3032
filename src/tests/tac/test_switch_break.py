"""`switch` como en TypeScript: los casos caen en el siguiente salvo que terminen
en `break`, que salta al final del switch. `continue` sigue siendo del bucle
(ver docs/tac.md §6.7)."""
from conftest import compile_tac


def _tac(source: str) -> list[str]:
    errors, tac = compile_tac(source)
    assert errors == [] and tac is not None
    return [line.strip() for line in tac]


def _after(tac: list[str], text: str) -> str:
    return tac[tac.index(text) + 1]


def test_case_without_break_falls_through():
    tac = _tac(
        'let x: integer = 1;\n'
        'switch (x) { case 1: print("uno"); case 2: print("dos"); default: print("otro"); }'
    )
    assert not _after(tac, 'print "uno"').startswith("goto")
    assert not _after(tac, 'print "dos"').startswith("goto")


def test_break_jumps_to_the_end_of_the_switch():
    tac = _tac(
        'let x: integer = 1;\n'
        'switch (x) { case 1: print("uno"); break; case 2: print("dos"); }\n'
        'print("fin");'
    )
    target = _after(tac, 'print "uno"').replace("goto ", "") + ":"
    assert target in tac
    assert tac[tac.index(target) + 1] == 'print "fin"'  # el final del switch


def test_break_in_switch_inside_loop_exits_the_switch_not_the_loop():
    tac = _tac(
        "let i: integer = 0;\n"
        "while (i < 3) {\n"
        '  switch (i) { case 1: break; default: print("d"); }\n'
        "  i = i + 1;\n"
        "}"
    )
    body = tac.index('print "d"')
    # ... goto Lend / Ldefault: / print "d" / Lend: / $t1 = i + 1 (el cuerpo del while sigue)
    break_jump = tac[body - 2]
    assert break_jump.startswith("goto L")
    switch_end = tac[body + 1]
    assert switch_end == break_jump.replace("goto ", "") + ":"
    assert tac[body + 2] == "$t1 = i + 1"


def test_continue_in_switch_inside_loop_targets_the_loop():
    tac = _tac(
        "let i: integer = 0;\n"
        "while (i < 3) {\n"
        "  i = i + 1;\n"
        "  switch (i) { case 1: continue; default: print(i); }\n"
        "}"
    )
    loop_condition = tac[tac.index("i = 0") + 1]  # L1:
    assert loop_condition.endswith(":")
    # el `continue` y el salto de regreso del while van a la misma etiqueta
    assert tac.count("goto " + loop_condition[:-1]) == 2


def test_break_inside_try_in_switch_emits_endtry():
    tac = _tac(
        "let x: integer = 1;\n"
        "switch (x) { case 1: try { break; } catch (e) { print(e); } default: print(x); }"
    )
    i = tac.index("try " + next(l.split()[1] for l in tac if l.startswith("try ")))
    assert tac[i + 1] == "endtry" and tac[i + 2].startswith("goto L")
