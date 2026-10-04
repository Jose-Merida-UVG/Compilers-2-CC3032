"""Core Compiscript lexing/parsing logic.

Shared by the CLI (main.py) and the HTTP backend (server.py) so both stay in
sync — there's exactly one place that knows how to lex/parse a Compiscript
source and turn the result into errors + a parse tree.
"""
from antlr4 import FileStream, InputStream, CommonTokenStream
from antlr4.tree.Tree import TerminalNode

from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from error_listener import CompiscriptErrorListener
from semantic.checker import SemanticChecker
from semantic.layout import assign_layout
from semantic.symbols import Scope
from tac.generator import TACGenerator

SUCCESS_MESSAGE = (
    "El archivo fue analizado correctamente. "
    "No se encontraron errores léxicos ni sintácticos."
)


def _tree_to_dict(node, rule_names: list[str]) -> dict:
    """Convert an ANTLR parse tree node into a plain dict tree, JSON-friendly
    for the frontend's parse-tree viewer."""
    if isinstance(node, TerminalNode):
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

    if errors:
        n = len(errors)
        noun = "error" if n == 1 else "errores"
        status_message = (
            f"Se encontraron {n} {noun} durante el análisis. "
            "No se generó código intermedio."
        )
    else:
        status_message = (
            f"{SUCCESS_MESSAGE} "
            f"Código intermedio generado ({tac_stats['instructions']} instrucciones)."
        )
 
    return {
        "errors": errors,
        "status_message": status_message,
        "tree_json": _tree_to_dict(tree, parser.ruleNames),
        "symbol_table_json": symbol_table_json,
        "tac": tac,
        "tac_stats": tac_stats,
    }


def analyze_file(path: str) -> dict:
    """Lex + parse a Compiscript source file on disk."""
    return analyze(FileStream(path, encoding="utf-8"))
