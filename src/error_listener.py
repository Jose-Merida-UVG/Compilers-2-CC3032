import re

from antlr4.error.ErrorListener import ErrorListener
from antlr4.Lexer import Lexer

FRIENDLY_TOKEN_NAMES = {
    "Identifier": "un identificador",
    "Literal": "un literal (número o cadena de texto)",
    "IntegerLiteral": "un número entero",
    "StringLiteral": "una cadena de texto",
    "EOF": "el fin del archivo",
}

MAX_EXPECTED = 6


class CompiscriptErrorListener(ErrorListener):
    """Recolecta errores léxicos y sintácticos, en español y con el detalle
    necesario para que el usuario los entienda y los ubique en el archivo."""

    def __init__(self):
        super().__init__()
        self.errors = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        if isinstance(recognizer, Lexer):
            self._lexical_error(recognizer, line, column, msg)
        else:
            self._syntax_error(recognizer, offendingSymbol, line, column, msg, e)

    # ── errores léxicos ──────────────────────────────────────────────────

    def _lexical_error(self, recognizer, line, column, msg):
        # `recognizer.text` suele venir vacío en este punto porque el token
        # todavía no se ha consumido. El texto real del carácter/lexema que
        # falló sí viene embebido en `msg`, que ANTLR arma como:
        #   "token recognition error at: '@'"
        match = re.search(r"token recognition error at: '(.*)'", msg)
        bad_text = match.group(1) if match else recognizer.text
        # ANTLR a veces incluye un carácter de más de contexto (p. ej. un
        # espacio) al reportar el intento fallido; se recorta para que el
        # mensaje muestre solo el símbolo relevante.
        bad_text = bad_text.strip() or bad_text

        self.errors.append(
            f"Error léxico en línea {line}, columna {column}: "
            f"carácter o secuencia no reconocida '{bad_text}'."
        )

    # ── errores sintácticos ──────────────────────────────────────────────

    def _syntax_error(self, recognizer, offendingSymbol, line, column, msg, e):
        found = self._describe_found(recognizer, offendingSymbol)
        expected_names = self._expected_names(recognizer)

        detail = f"se encontró {found}"
        if expected_names:
            shown = expected_names[:MAX_EXPECTED]
            detail += f", pero se esperaba " + self._join_expected(shown)
            if len(expected_names) > MAX_EXPECTED:
                detail += ", entre otros"

        self.errors.append(
            f"Error sintáctico en línea {line}, columna {column}: {detail}."
        )

    def _describe_found(self, recognizer, offendingSymbol):
        if offendingSymbol is None or offendingSymbol.text is None:
            return "el fin del archivo"
        text = offendingSymbol.text
        friendly = self._token_type_name(recognizer, offendingSymbol.type)
        return f"'{text}'" if friendly is None else f"{friendly} ('{text}')"

    def _token_type_name(self, recognizer, token_type):
        """Nombre amigable en español para un tipo de token (por ejemplo
        Identifier -> 'un identificador'), o None si es un token literal
        que ya se lee bien tal cual ('if', '+', etc.)."""
        symbolic = (
            recognizer.symbolicNames[token_type]
            if token_type < len(recognizer.symbolicNames) and recognizer.symbolicNames[token_type]
            else None
        )
        if symbolic and symbolic != "<INVALID>" and symbolic in FRIENDLY_TOKEN_NAMES:
            return FRIENDLY_TOKEN_NAMES[symbolic]
        return None

    def _expected_names(self, recognizer):
        names = []
        try:
            expected = recognizer.getExpectedTokens()
            for t in expected:
                if t == -1:
                    continue
                symbolic = (
                    recognizer.symbolicNames[t]
                    if t < len(recognizer.symbolicNames) and recognizer.symbolicNames[t]
                    else None
                )
                if symbolic and symbolic != "<INVALID>":
                    names.append(FRIENDLY_TOKEN_NAMES.get(symbolic, symbolic))
                elif (
                    t < len(recognizer.literalNames)
                    and recognizer.literalNames[t]
                    and recognizer.literalNames[t] != "<INVALID>"
                ):
                    names.append(recognizer.literalNames[t])
        except Exception:
            pass
        seen = set()
        unique = []
        for n in names:
            if n not in seen:
                seen.add(n)
                unique.append(n)
        return unique

    @staticmethod
    def _join_expected(names):
        if len(names) == 1:
            return names[0]
        return ", ".join(names[:-1]) + " o " + names[-1]

    def has_errors(self):
        return len(self.errors) > 0
