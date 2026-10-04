"""Invariantes de la tabla de símbolos sobre todos los casos válidos de todas
las áreas: ningún símbolo de datos queda sin tamaño/offset/dirección, nada se
solapa dentro de un área, todo está alineado, los frames suman y los campos
heredados quedan donde estaban en el padre.
"""
import glob
import os
import re

import pytest
from antlr4 import CommonTokenStream, InputStream

from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from semantic.checker import SemanticChecker
from semantic.layout import SAVED_SIZE, assign_layout
from semantic.symbols import Scope, ScopeKind, SymbolKind
from tac.generator import TACGenerator

_TAC_TESTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
_VALID = sorted(glob.glob(os.path.join(_TAC_TESTS, "*", "valido_*.cps")))
_DATA = (SymbolKind.VARIABLE, SymbolKind.CONSTANT, SymbolKind.PARAMETER)


def _laid_out(path: str):
    with open(path, encoding="utf-8") as f:
        parser = CompiscriptParser(CommonTokenStream(CompiscriptLexer(InputStream(f.read()))))
    tree = parser.program()
    checker = SemanticChecker()
    assert checker.check(tree).as_strings() == []
    generator = TACGenerator(checker)
    tac = generator.visit(tree)
    assign_layout(checker.symbols.global_scope, generator.e.max_temps, generator.name_of)
    return checker.symbols.global_scope, generator, tac


def _all_scopes(scope: Scope):
    yield scope
    for child in scope.children:
        yield from _all_scopes(child)


def _own_data(scope: Scope, kinds=(SymbolKind.VARIABLE, SymbolKind.CONSTANT)):
    """Símbolos de datos de `scope` y de sus bloques, sin entrar a funciones
    ni clases anidadas (cada una tiene su propia área)."""
    found = [s for s in scope.symbols.values() if s.kind in kinds]
    for child in scope.children:
        if child.kind is ScopeKind.BLOCK:
            found += _own_data(child, kinds)
    return found


def _assert_area(symbols, where: str) -> None:
    spans = sorted((s.offset, s.offset + s.size, s.name) for s in symbols)
    for (start, end, name), (next_start, _, next_name) in zip(spans, spans[1:]):
        assert end <= next_start, f"{where}: {name} y {next_name} se solapan"
    for s in symbols:
        assert s.offset % s.size == 0, f"{where}: {s.name} sin alinear"


@pytest.mark.parametrize("path", _VALID, ids=lambda p: os.path.relpath(p, _TAC_TESTS))
def test_symbol_table_invariants(path):
    root, generator, tac = _laid_out(path)

    for scope in _all_scopes(root):
        for symbol in scope.symbols.values():
            if symbol.kind in _DATA:
                assert None not in (symbol.size, symbol.offset, symbol.address), symbol.name
            if symbol.kind in (SymbolKind.FUNCTION, SymbolKind.CLASS):
                assert symbol.label, f"{symbol.name} sin etiqueta"

    # __main: sus variables son globales, así que su frame solo guarda temporales y ra/fp
    main = root.frame
    assert main["label"] == "__main"
    assert main["params_size"] == 0 and main["locals_size"] == 0
    assert main["temps"] == generator.e.max_temps("__main")
    assert main["total_size"] == main["temps_size"] + main["saved_size"]

    # Todo nombre de variable que usa el TAC tiene un símbolo con ese tac_name
    tac_names = {s.tac_name for sc in _all_scopes(root) for s in sc.symbols.values()}
    assert None not in tac_names
    keywords = {"func", "endfunc", "class", "endclass", "goto", "if", "ifFalse", "param", "call",
                "return", "print", "new", "newarray", "len", "itof", "try", "endtry", "catch",
                "true", "false", "null", "this"}
    for line in tac:
        text = line.strip()
        if text.startswith(("func ", "class ")) or re.fullmatch(r"L\d+:", text):
            continue
        text = re.sub(r"\$t\d+", "", re.sub(r'"(?:[^"\\]|\\.)*"', "", text))
        for word in re.findall(r"[A-Za-z_]\w*(?:\.\w+)*", text):
            if "." in word or word in keywords or re.fullmatch(r"L\d+", word):
                continue
            assert word in tac_names, f"`{word}` del TAC no tiene símbolo"

    _assert_area(_own_data(root), "globales")
    for s in _own_data(root):
        assert s.address == f"gp+{s.offset}"

    for scope in _all_scopes(root):
        if scope.kind is ScopeKind.FUNCTION:
            frame = scope.frame
            params = [s for s in scope.symbols.values() if s.kind is SymbolKind.PARAMETER]
            locals_ = _own_data(scope)
            _assert_area(params, f"parámetros de {frame['label']}")
            _assert_area(locals_, f"locales de {frame['label']}")
            for s in params:
                assert s.address == f"fp+{SAVED_SIZE + s.offset}"
            for s in locals_:
                assert s.address == f"fp-{s.offset + s.size}"

            assert frame["params_size"] % 4 == 0 and frame["locals_size"] % 4 == 0
            assert frame["params_size"] >= max([s.offset + s.size for s in params], default=0)
            assert frame["locals_size"] >= max([s.offset + s.size for s in locals_], default=0)
            assert frame["temps_size"] == frame["temps"] * 4
            assert frame["total_size"] == (
                frame["params_size"] + frame["locals_size"] + frame["temps_size"] + frame["saved_size"]
            )
            # `temps` viene del pico que midió el Emitter para esa función
            assert frame["temps"] == generator.e.max_temps(frame["label"]), frame["label"]

        if scope.kind is ScopeKind.CLASS:
            layout = scope.layout
            fields = [s for s in scope.symbols.values() if s.kind in (SymbolKind.VARIABLE, SymbolKind.CONSTANT)]
            _assert_area(fields, f"campos de {scope.owner}")
            for s in fields:
                assert s.address == f"this+{s.offset}"
            assert layout["size"] % 4 == 0
            assert layout["size"] >= max([f["offset"] + f["size"] for f in layout["fields"]], default=0)
            assert root.symbols[scope.owner].size == layout["size"]

            if layout["parent"]:
                parent = next(
                    sc.layout for sc in _all_scopes(root)
                    if sc.kind is ScopeKind.CLASS and sc.owner == layout["parent"]
                )
                inherited = [f for f in layout["fields"] if f["inherited"]]
                own = [f for f in layout["fields"] if not f["inherited"]]
                assert [(f["name"], f["offset"], f["size"]) for f in inherited] == [
                    (f["name"], f["offset"], f["size"]) for f in parent["fields"]
                ], f"{scope.owner} no conserva los offsets del padre"
                assert all(f["offset"] >= parent["size"] for f in own)
