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


def analyze(input_stream: InputStream) -> dict:
    """Lex + parse a Compiscript ANTLR input stream.
 
    Returns a dict with:
      - errors: list[str]      lexical/syntax error messages (empty if none)
      - status_message: str    Spanish message: success text if no errors,
                                otherwise a summary of how many were found
      - tree_json: dict        parse tree as a nested dict, for visualization
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
    if not errors:
        semantic_errors = SemanticChecker().check(tree)
        errors.extend(semantic_errors.as_strings())

    if errors:
        n = len(errors)
        noun = "error" if n == 1 else "errores"
        status_message = f"Se encontraron {n} {noun} durante el análisis."
    else:
        status_message = SUCCESS_MESSAGE
 
    return {
        "errors": errors,
        "status_message": status_message,
        "tree_json": _tree_to_dict(tree, parser.ruleNames),
    }


def analyze_file(path: str) -> dict:
    """Lex + parse a Compiscript source file on disk."""
    return analyze(FileStream(path, encoding="utf-8"))
