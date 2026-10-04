"""FunctionMixin: TAC de funciones, retorno y llamadas.

Cada función es una unidad del Emitter con su propio pool de temporales; las
anidadas se emiten después de la contenedora y los métodos reciben `this` como
primer parámetro. Una llamada evalúa todos sus argumentos antes de emitir los
`param`, para que las llamadas anidadas no intercalen los suyos. La cadena
`leftHandSide` (gen_classes.py) usa `_emit_call` por cada `( )`.
"""

from __future__ import annotations

from typing import Optional

from CompiscriptParser import CompiscriptParser

from semantic.symbols import ScopeKind
from semantic.types import FunctionType, Type, VoidType
from tac.instructions import END_FUNCTION, call_instruction, function_header


class FunctionMixin:
    def _return_types(self) -> list:
        # Pila de tipos de retorno; se crea aquí porque un mixin no tiene __init__
        if not hasattr(self, "_fn_return_types"):
            self._fn_return_types: list = []
        return self._fn_return_types

    def visitFunctionDeclaration(self, ctx: CompiscriptParser.FunctionDeclarationContext):
        symbol = self.symbol_of(ctx)
        label = self.name_of(symbol) if symbol is not None else ctx.Identifier().getText()

        names = []
        if ctx.parameters() is not None:
            for param_ctx in ctx.parameters().parameter():
                param = self.symbol_of(param_ctx)
                names.append(
                    self.name_of(param) if param is not None
                    else param_ctx.Identifier().getText()
                )
        if self.scope_of(ctx).kind is ScopeKind.CLASS:
            names.insert(0, "this")

        return_type = (
            symbol.type.ret
            if symbol is not None and isinstance(symbol.type, FunctionType)
            else None
        )

        # break, continue y try de la función contenedora no valen adentro
        saved = (self.break_labels, self.continue_labels, getattr(self, "open_tries", 0))
        self.break_labels, self.continue_labels = [], []
        self.open_tries = 0
        self._return_types().append(return_type)
        self.e.begin_unit(function_header(label, names))
        try:
            self.visit(ctx.block())
            # Sin return garantizado se agrega uno, para no caer por el final
            if not self._always_returns(ctx.block()):
                self.e.emit("return")
            self.e.end_unit(END_FUNCTION)
        finally:
            self._return_types().pop()
            self.break_labels, self.continue_labels, self.open_tries = saved
        return None

    @classmethod
    def _always_returns(cls, node) -> bool:
        """Mismo criterio que el checker: un return, un bloque que contiene
        uno, o un if/else cuyas dos ramas retornan."""
        P = CompiscriptParser
        if isinstance(node, P.ReturnStatementContext):
            return True
        if isinstance(node, P.BlockContext):
            return any(cls._always_returns(st) for st in node.statement())
        if isinstance(node, P.IfStatementContext):
            blocks = node.block()
            return len(blocks) == 2 and all(cls._always_returns(b) for b in blocks)
        if isinstance(node, P.StatementContext):
            return cls._always_returns(node.getChild(0))
        return False

    def visitReturnStatement(self, ctx: CompiscriptParser.ReturnStatementContext):
        value: Optional[str] = None
        if ctx.expression() is not None:
            value = self.expr(ctx.expression())
            expected = self._return_types()[-1] if self._return_types() else None
            value = self._coerce(value, self.type_of(ctx.expression()), expected)
        # El valor se calcula dentro del try y luego se sale de él
        for _ in range(getattr(self, "open_tries", 0)):
            self.e.emit("endtry")
        self.e.emit(f"return {value}" if value is not None else "return")
        self.e.free(value)
        return None

    def _eval_args(self, arguments, param_types: list[Type]) -> list[str]:
        """Evalúa los argumentos en orden y devuelve sus operandos, sin `param`."""
        values = []
        for index, arg in enumerate(arguments.expression() if arguments else []):
            value = self.expr(arg)
            if index < len(param_types):
                value = self._coerce(value, self.type_of(arg), param_types[index])
            values.append(value)
        return values

    def _push_params(self, operands: list[str]) -> None:
        for operand in operands:
            self.e.emit(f"param {operand}")
            self.e.free(operand)

    def _emit_call(
        self,
        callee: str,
        call_ctx,
        callee_type: Optional[Type],
        receiver: Optional[str] = None,
        statement: bool = False,
    ) -> Optional[str]:
        """Emite la llamada; `receiver` es el objeto de un método y cuenta como
        primer argumento. Devuelve el temporal del resultado o None si no hay."""
        function = callee_type if isinstance(callee_type, FunctionType) else None
        args = self._eval_args(call_ctx.arguments(), function.params if function else [])

        count = len(args)
        if receiver is not None:
            self._push_params([receiver])
            count += 1
        self._push_params(args)
        self.e.free(callee)

        # Sin destino si el valor se descarta o la función es void
        if statement or (function is not None and isinstance(function.ret, VoidType)):
            self.e.emit(call_instruction(callee, count))
            return None
        result = self.e.new_temp()
        self.e.emit(call_instruction(callee, count, result))
        return result

    @staticmethod
    def _is_statement(ctx) -> bool:
        """¿La expresión es, completa, una sentencia `expr;`?"""
        node = ctx.parentCtx
        while node is not None and node.getChildCount() == 1:
            node = node.parentCtx
        return isinstance(node, CompiscriptParser.ExpressionStatementContext)
