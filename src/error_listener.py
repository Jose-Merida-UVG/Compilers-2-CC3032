from antlr4.error.ErrorListener import ErrorListener
from antlr4.Lexer import Lexer


class CompiscriptErrorListener(ErrorListener):
    """Collects lexical and syntax errors, tagged and with concrete detail."""

    def __init__(self):
        super().__init__()
        self.errors = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        if isinstance(recognizer, Lexer):
            self._lexical_error(recognizer, line, column, msg)
        else:
            self._syntax_error(recognizer, offendingSymbol, line, column, msg, e)

    def _lexical_error(self, recognizer, line, column, msg):
        # msg is ANTLR's default, e.g. "token recognition error at: '@'"
        bad_text = recognizer.text
        self.errors.append(
            f"[LEXICAL] line {line}:{column} unrecognized character or malformed token "
            f"near '{bad_text}'"
        )

    def _syntax_error(self, recognizer, offendingSymbol, line, column, msg, e):
        found = offendingSymbol.text if offendingSymbol is not None else "<EOF>"

        expected_names = []
        try:
            expected = recognizer.getExpectedTokens()
            expected_names = [
                recognizer.symbolicNames[t] if t < len(recognizer.symbolicNames) and recognizer.symbolicNames[t]
                else recognizer.literalNames[t]
                for t in expected.toList()
                if t != -1
            ]
        except Exception:
            pass

        kind = type(e).__name__ if e is not None else "SyntaxError"

        detail = f"unexpected '{found}'"
        if expected_names:
            detail += f", expected one of: {', '.join(expected_names)}"

        self.errors.append(f"[SYNTAX:{kind}] line {line}:{column} {detail}")

    def has_errors(self):
        return len(self.errors) > 0
