"""Invariantes estructurales del TAC, sobre todos los casos válidos de todas
las áreas: propiedades que cualquier TAC correcto debe cumplir.

  * Cada `call f, n` va precedido por exactamente `n` `param` seguidos.
  * Si `f` es una función conocida, `n` coincide con su número de parámetros.
  * Toda etiqueta usada está definida una sola vez en su función.
  * Toda función (salvo `__main`) termina en `return`.
  * El mayor `$tN` de cada función es su pico de temporales: el reciclaje usa
    siempre el menor índice libre, así que no quedan huecos ni fugas.
"""
import glob
import os
import re

import pytest
from antlr4 import CommonTokenStream, InputStream

from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from semantic.checker import SemanticChecker
from tac.generator import TACGenerator

_HERE = os.path.dirname(os.path.abspath(__file__))
_VALID = sorted(glob.glob(os.path.join(_HERE, "*", "valido_*.cps")))

_FUNC = re.compile(r"func ([^\s(]+)\((.*)\):")
_CALL = re.compile(r"(?:\$t\d+ = )?call(virt)? (\S+), (\d+)")
_TEMP = re.compile(r"\$t(\d+)")
_LABEL_USE = re.compile(r"(?:goto|try) (L\d+)$")
_LABEL_DEF = re.compile(r"(L\d+):$")


def _generate(path: str):
    with open(path, encoding="utf-8") as f:
        parser = CompiscriptParser(CommonTokenStream(CompiscriptLexer(InputStream(f.read()))))
    tree = parser.program()
    checker = SemanticChecker()
    assert checker.check(tree).as_strings() == []
    generator = TACGenerator(checker)
    return generator.visit(tree), generator


def _units(tac: list[str]) -> list[tuple[str, int, list[str]]]:
    """(nombre, nº de parámetros, instrucciones) de cada `func`."""
    units, current = [], None
    for line in tac:
        header = _FUNC.fullmatch(line)
        if header:
            params = [p for p in header.group(2).split(",") if p.strip()]
            current = (header.group(1), len(params), [])
        elif line == "endfunc":
            units.append(current)
            current = None
        elif current is not None:
            current[2].append(line)
    return units


@pytest.mark.parametrize("path", _VALID, ids=lambda p: os.path.relpath(p, _HERE))
def test_tac_invariants(path):
    tac, generator = _generate(path)
    units = _units(tac)
    arity = {name: params for name, params, _ in units}

    for name, _, body in units:
        instructions = [line.strip() for line in body]

        for index, line in enumerate(instructions):
            call = _CALL.fullmatch(line)
            if not call:
                continue
            callee, count = call.group(2), int(call.group(3))
            pushed = 0
            while index - pushed - 1 >= 0 and instructions[index - pushed - 1].startswith("param "):
                pushed += 1
            assert pushed == count, f"{name}: `{line}` tiene {pushed} param seguidos"
            if call.group(1):  # callvirt: el destino es un temporal con la tabla
                assert instructions[index - pushed - 1].startswith(f"{callee} = "), line
            elif callee in arity:
                assert count == arity[callee], f"{name}: `{line}` y {callee} tiene {arity[callee]} parámetros"

        defined = [m.group(1) for line in body if (m := _LABEL_DEF.fullmatch(line))]
        assert len(defined) == len(set(defined)), f"{name}: etiqueta repetida"
        used = {m.group(1) for line in instructions if (m := _LABEL_USE.search(line))}
        used |= {m.group(1) for line in instructions
                 for m in re.finditer(r"goto (L\d+)", line)}
        assert used <= set(defined), f"{name}: etiquetas sin definir {used - set(defined)}"

        if name != "__main":
            assert instructions[-1].startswith("return"), f"{name} no termina en return"

        highest = max((int(n) for line in instructions for n in _TEMP.findall(line)), default=0)
        assert highest == generator.e.max_temps(name), f"{name}: pico de temporales distinto"
