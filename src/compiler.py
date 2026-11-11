"""Core Compiscript lexing/parsing logic.

Shared by the CLI (main.py) and the HTTP backend (server.py) so both stay in
sync — there's exactly one place that knows how to lex/parse a Compiscript
source and turn the result into errors + a parse tree.
"""
from __future__ import annotations

from asm.generator import generate_asm

from antlr4 import FileStream, InputStream, CommonTokenStream
from antlr4.tree.Tree import TerminalNodeImpl

from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from error_listener import CompiscriptErrorListener
from semantic.checker import SemanticChecker
from semantic.layout import assign_layout
from semantic.symbols import Scope
from tac.generator import TACGenerator

def optimize(lines: list[str]) -> tuple[list[str], dict[str, int]]:
    """Usa la mirilla de Tono; identidad solamente si el módulo no existe."""
    try:
        from asm.peephole import optimize as optimize_mips
    except ModuleNotFoundError as exc:
        if exc.name != "asm.peephole":
            raise
        return list(lines), {}
    return optimize_mips(lines)


def _asm_instruction_count(lines: list[str]) -> int:
    """Cuenta instrucciones en .text, excluyendo comentarios y directivas."""
    count = 0
    in_text = False
    for line in lines:
        text = line.split("#", 1)[0].strip()
        if text.startswith(".text"):
            in_text = True
        elif text.startswith(".data"):
            in_text = False
        if not in_text or not text or text.startswith("."):
            continue
        if ":" in text:
            text = text.split(":", 1)[1].strip()
        if text and not text.startswith("."):
            count += 1
    return count


SUCCESS_MESSAGE = (
    "El archivo fue analizado correctamente. "
    "No se encontraron errores léxicos ni sintácticos."
)


def _tree_to_dict(node, rule_names: list[str]) -> dict:
    """Convert an ANTLR parse tree node into a plain dict tree, JSON-friendly
    for the frontend's parse-tree viewer."""
    if isinstance(node, TerminalNodeImpl):
        return {"label": node.getText(), "isTerminal": True, "children": []}
    name = rule_names[node.getRuleIndex()]
    return {
        "label": name,
        "isTerminal": False,
        "children": [_tree_to_dict(node.getChild(i), rule_names) for i in range(node.getChildCount())],
    }


def _frame_temps(scope: Scope) -> int:
    """Mayor cantidad de temporales entre los frames del subárbol."""
    own = scope.frame["temps"] if scope.frame else 0
    return max([own] + [_frame_temps(child) for child in scope.children])


def _tac_stats(tac: list[str], generator: TACGenerator, global_scope: Scope) -> dict:
    """Resumen del TAC: instrucciones (sin cabeceras ni cierres de func/class),
    pico de temporales de una sola función y cantidad de unidades `func`."""
    structure = ("func ", "endfunc", "class ", "endclass")
    return {
        "instructions": sum(1 for line in tac if not line.startswith(structure)),
        "temps": _frame_temps(global_scope),
        "functions": sum(1 for line in tac if line.startswith("func ")),
    }

def analyze(input_stream: InputStream) -> dict:
    """Analiza un fuente Compiscript: léxico, sintaxis, semántica y, sin
    errores, código intermedio.

    Devuelve un dict con:
      - errors: list[str]      errores léxicos, sintácticos y semánticos
      - status_message: str    mensaje en español: éxito o conteo de errores
      - tree_json: dict        árbol sintáctico, para el visor del árbol
      - symbol_table_json: dict | None  árbol de ámbitos (Scope.to_dict) con
                               el layout de semantic/layout.py; None si el
                               análisis semántico no corrió
      - tac: list[str] | None  código de tres direcciones; None con cualquier
                               error (no se genera TAC)
      - tac_stats: dict | None {"instructions", "temps", "functions"} del TAC
    """
    lexer = CompiscriptLexer(input_stream)
 
    error_listener = CompiscriptErrorListener()
    lexer.removeErrorListeners()
    lexer.addErrorListener(error_listener)
 
    tokens = CommonTokenStream(lexer)
    parser = CompiscriptParser(tokens)
    parser.removeErrorListeners()
    parser.addErrorListener(error_listener)
 
    tree = parser.program()

    errors = list(error_listener.errors)

    # Semantic analysis only runs on a clean tree: if ANTLR had to
    # error-recover through lexical/syntax errors, walking the result would
    # likely produce noisy, misleading semantic errors on top of the real
    # ones (see semantic/checker.py's module docstring).
    #
    # The checker instance (not just its errors) is kept around afterward
    # so its symbol table -- a real Scope tree, see semantic/symbols.py --
    # can be serialized below for the IDE's symbol-table panel. None (not
    # an empty tree) when semantic analysis didn't run at all, so the
    # frontend can tell "no symbols" apart from "didn't get this far".
    symbol_table_json = None
    tac = None
    tac_stats = None
    asm = asm_raw = asm_stats = activation = None
    if not errors:
        checker = SemanticChecker()
        semantic_errors = checker.check(tree)
        errors.extend(semantic_errors.as_strings())
        global_scope = checker.symbols.global_scope

        generator = None
        if not errors:
            # El layout necesita los temporales del TAC, por eso va después
            try:
                generator = TACGenerator(checker)
                tac = generator.visit(tree)
            except Exception as exc:  # un fallo del generador no debe tumbar el IDE
                tac = None
                errors.append(f"Error interno al generar el código intermedio: {exc}")

        if generator and tac:
            assign_layout(global_scope, generator.e.max_temps, generator.name_of)
        else:
            assign_layout(global_scope)
        symbol_table_json = global_scope.to_dict()
        if tac is not None and generator is not None:
            tac_stats = _tac_stats(tac, generator, global_scope)

    if not errors and tac is not None and symbol_table_json is not None:
        try:
            # La única entrada de P3 es TAC textual + JSON de símbolos.
            generated = generate_asm(tac, symbol_table_json)
            raw = list(generated.lines)
            optimized, changes = optimize(list(raw))
            stats = {
                "instructions_raw": _asm_instruction_count(raw),
                "instructions": _asm_instruction_count(optimized),
                "peephole": changes,
            }
            # Publicar resultados solamente cuando toda la fase termina.
            asm_raw = raw
            asm = optimized
            asm_stats = stats
            activation = generated.activation
        except Exception as exc:
            errors.append(f"Error interno al generar el ensamblador: {exc}")
            tac = tac_stats = None
            asm = asm_raw = asm_stats = activation = None

    if errors:
        n = len(errors)
        noun = "error" if n == 1 else "errores"
        status_message = (
            f"Se encontraron {n} {noun} durante el análisis. "
            "No se generó código intermedio ni ensamblador."
        )
    else:
        # Sin errores el TAC y el ensamblador existen: si hubieran fallado,
        # arriba se habría agregado un error.
        assert tac_stats is not None and asm_stats is not None
        status_message = (
            f"{SUCCESS_MESSAGE} "
            f"Código intermedio generado ({tac_stats['instructions']} instrucciones). "
            f"Ensamblador generado ({asm_stats['instructions']} instrucciones)."
        )
 
    return {
        "errors": errors,
        "status_message": status_message,
        "tree_json": _tree_to_dict(tree, parser.ruleNames),
        "symbol_table_json": symbol_table_json,
        "tac": tac,
        "tac_stats": tac_stats,
        "asm": asm,
        "asm_raw": asm_raw,
        "asm_stats": asm_stats,
        "activation": activation,
    }


def analyze_file(path: str) -> dict:
    """Lex + parse a Compiscript source file on disk."""
    return analyze(FileStream(path, encoding="utf-8"))

