"""Los casos de un `switch` son excluyentes: cada cuerpo salta al final, sin caer
en el siguiente (ver docs/tac.md §6.7)."""
from conftest import compile_tac


def _tac(source: str) -> list[str]:
    errors, tac = compile_tac(source)
    assert errors == [] and tac is not None
    return [line.strip() for line in tac]


def test_each_case_jumps_to_the_end():
    tac = _tac(
        'let x: integer = 1;\n'
        'switch (x) { case 1: print("uno"); case 2: print("dos"); default: print("otro"); }'
    )
    uno, dos, otro = (tac.index(f'print "{w}"') for w in ("uno", "dos", "otro"))
    assert tac[uno + 1].startswith("goto L")
    assert tac[dos + 1] == tac[uno + 1]  # ambos saltan al mismo final
    assert tac[otro + 1] == tac[uno + 1].replace("goto ", "") + ":"


def test_last_case_without_default_has_no_goto():
    tac = _tac('let x: integer = 1;\nswitch (x) { case 1: print("a"); case 2: print("b"); }')
    assert not tac[tac.index('print "b"') + 1].startswith("goto")


def test_case_ending_in_return_has_no_dead_goto():
    tac = _tac(
        "function f(x: integer): integer {\n"
        "  switch (x) { case 1: return 1; default: return 2; }\n"
        "  return 0;\n}"
    )
    assert not any(a.startswith("return") and b.startswith("goto") for a, b in zip(tac, tac[1:]))
