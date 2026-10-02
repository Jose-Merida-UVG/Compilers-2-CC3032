"""CoreMixin: TAC para declaraciones, asignaciones, expresiones y print.

Reglas de la gramática que implementa (ver docs/proyecto2/00-contrato.md
§4.1): variableDeclaration, constantDeclaration, assignment,
expressionStatement, printStatement, AssignExpr, literalExpr, primaryExpr,
IdentifierExpr, additiveExpr, multiplicativeExpr y unaryExpr.

Convención: cada visit de expresión devuelve un *operando* (str): una
variable, un temporal `$tN` o una constante literal. Quien consume un
operando lo libera con `self.e.free(op)` apenas emite la instrucción que lo
usa (reciclaje de temporales, contrato §4.2).

Depende solo de la API del contrato: `self.e` (Emitter), `self.expr`,
`self.type_of`, `self.symbol_of`, `self.name_of`.

── Notas para quien integre (Cami: esqueleto/checker, Tono: funciones y
   clases) ─────────────────────────────────────────────────────────────

1. Anotaciones del checker: sobrescribir solo `visit()` NO basta. El
   visitor por defecto (`visitChildren`, p. ej. en `statement`) llama
   `child.accept()` directo y se salta `visit()`; hay que sobrescribir
   también `visitChildren` para que pase por `self.visit(child)`. Sin eso
   faltan tipos/ámbitos en declaraciones y sentencias.
2. `symbol_of(ctx)` se llama con: IdentifierExpr, variableDeclaration,
   constantDeclaration, assignment (forma simple) y, para AssignExpr con
   identificador simple, el `leftHandSide` (`lhs`). Si devuelve None se
   usa el texto del identificador (sin renombrar por sombreado).
3. `type_of(ctx)` se usa para la promoción integer->float (`itof`); si
   devuelve None simplemente no se promueve.
4. Una expresión `void` (llamada a función sin retorno) puede devolver
   None desde `visit`; `expressionStatement` solo libera si hay operando.
5. `visitAssignExpr` y `visitAssignment` no tocan temporales ajenos:
   devuelven la variable asignada (no es temporal, `free` es no-op).
"""

from __future__ import annotations

import re
from typing import Optional

from CompiscriptParser import CompiscriptParser

from semantic.types import FloatType, IntegerType, StringType, Type

_INT_LITERAL = re.compile(r"-?\d+")
_NUM_LITERAL = re.compile(r"-?\d+(\.\d+)?")


class CoreMixin:
    # ── Utilidades ──────────────────────────────────────────────────────
    def _ident(self, ctx, text: str) -> str:
        """Nombre TAC de un identificador: el del símbolo resuelto (que
        resuelve el sombreado, `x_1`) o, si el checker no lo anotó, el
        texto tal cual."""
        symbol = self.symbol_of(ctx)
        return self.name_of(symbol) if symbol is not None else text

    def _coerce(self, op: str, src: Optional[Type], dst: Optional[Type]) -> str:
        """Promoción integer -> float. Constantes enteras se convierten
        en el acto (`5` -> `5.0`); lo demás pasa por `itof`."""
        if isinstance(dst, FloatType) and isinstance(src, IntegerType):
            if _INT_LITERAL.fullmatch(op):
                return op + ".0"
            self.e.free(op)
            t = self.e.new_temp()
            self.e.emit(f"{t} = itof {op}")
            return t
        return op

    @staticmethod
    def _numeric(t: Optional[Type]) -> bool:
        return isinstance(t, (IntegerType, FloatType))

    def _result_type(self, op: str, lt: Optional[Type], rt: Optional[Type]) -> Optional[Type]:
        if op in ("<", "<=", ">", ">=", "==", "!="):
            from semantic.types import BooleanType

            return BooleanType()
        if isinstance(lt, FloatType) or isinstance(rt, FloatType):
            return FloatType()
        if isinstance(lt, StringType) or isinstance(rt, StringType):
            return StringType()
        return lt

    def _binary_chain(self, ctx, operands) -> str:
        """`sub (OP sub)*` asociativo a la izquierda: un operando solo
        pasa de largo; con operadores se emite `t = a OP b` por cada
        paso, liberando los operandos *antes* de pedir el temporal del
        resultado para que `$t1 = $t1 + $t2` reutilice."""
        left = self.expr(operands[0])
        ltype = self.type_of(operands[0])
        for i in range(1, len(operands)):
            op = ctx.getChild(2 * i - 1).getText()
            right = self.expr(operands[i])
            rtype = self.type_of(operands[i])
            if self._numeric(ltype) and self._numeric(rtype):
                # integer mezclado con float: el entero se promueve
                if isinstance(ltype, FloatType) and isinstance(rtype, IntegerType):
                    right = self._coerce(right, rtype, ltype)
                elif isinstance(rtype, FloatType) and isinstance(ltype, IntegerType):
                    left = self._coerce(left, ltype, rtype)
            self.e.free(left)
            self.e.free(right)
            t = self.e.new_temp()
            self.e.emit(f"{t} = {left} {op} {right}")
            ltype = self._result_type(op, ltype, rtype)
            left = t
        return left

    # ── Declaraciones y asignación ──────────────────────────────────────
    def _declare(self, ctx, init_ctx) -> None:
        """Compartido por `let/var` y `const`. Sin inicializador no se
        emite nada: el TAC no inicializa por defecto."""
        if init_ctx is None:
            return None
        name = self._ident(ctx, ctx.Identifier().getText())
        value = self.expr(init_ctx)
        symbol = self.symbol_of(ctx)
        value = self._coerce(
            value, self.type_of(init_ctx), symbol.type if symbol is not None else None
        )
        self.e.emit(f"{name} = {value}")
        self.e.free(value)
        return None

    def visitVariableDeclaration(self, ctx: CompiscriptParser.VariableDeclarationContext):
        init = ctx.initializer()
        return self._declare(ctx, init.expression() if init is not None else None)

    def visitConstantDeclaration(self, ctx: CompiscriptParser.ConstantDeclarationContext):
        return self._declare(ctx, ctx.expression())

    def visitAssignment(self, ctx: CompiscriptParser.AssignmentContext):
        # Dos alternativas con el mismo contexto: `x = e;` (1 expresión) y
        # `obj.campo = e;` (2 expresiones: el objeto y el valor).
        exprs = ctx.expression()
        if len(exprs) == 1:
            name = self._ident(ctx, ctx.Identifier().getText())
            value = self.expr(exprs[0])
            symbol = self.symbol_of(ctx)
            value = self._coerce(
                value, self.type_of(exprs[0]), symbol.type if symbol is not None else None
            )
            self.e.emit(f"{name} = {value}")
            self.e.free(value)
            return None
        obj = self.expr(exprs[0])
        value = self.expr(exprs[1])
        self.e.emit(f"{obj}.{ctx.Identifier().getText()} = {value}")
        self.e.free(obj)
        self.e.free(value)
        return None

    def visitAssignExpr(self, ctx: CompiscriptParser.AssignExprContext):
        # `lhs = rhs` como expresión; aquí solo el caso de identificador
        # simple. Devuelve la variable asignada (no es temporal).
        lhs = ctx.lhs
        value = self.expr(ctx.assignmentExpr())
        name = self._ident(lhs, lhs.primaryAtom().getText())
        symbol = self.symbol_of(lhs)
        value = self._coerce(
            value, self.type_of(ctx.assignmentExpr()), symbol.type if symbol is not None else None
        )
        self.e.emit(f"{name} = {value}")
        self.e.free(value)
        return name

    def visitExpressionStatement(self, ctx: CompiscriptParser.ExpressionStatementContext):
        # El valor se descarta; una expresión de tipo void devuelve None.
        result = self.expr(ctx.expression())
        if result:
            self.e.free(result)
        return None

    def visitPrintStatement(self, ctx: CompiscriptParser.PrintStatementContext):
        value = self.expr(ctx.expression())
        self.e.emit(f"print {value}")
        self.e.free(value)
        return None

    # ── Átomos ──────────────────────────────────────────────────────────
    def visitLiteralExpr(self, ctx: CompiscriptParser.LiteralExprContext):
        if ctx.arrayLiteral() is not None:
            return self.visit(ctx.arrayLiteral())
        # Literal numérico/string, `null`, `true` o `false`: se emite tal
        # cual aparece en el fuente.
        return ctx.getText()

    def visitPrimaryExpr(self, ctx: CompiscriptParser.PrimaryExprContext):
        if ctx.literalExpr() is not None:
            return self.visit(ctx.literalExpr())
        if ctx.leftHandSide() is not None:
            return self.visit(ctx.leftHandSide())
        return self.expr(ctx.expression())  # '(' expression ')'

    def visitIdentifierExpr(self, ctx: CompiscriptParser.IdentifierExprContext):
        return self._ident(ctx, ctx.Identifier().getText())

    # ── Aritmética ──────────────────────────────────────────────────────
    def visitAdditiveExpr(self, ctx: CompiscriptParser.AdditiveExprContext):
        return self._binary_chain(ctx, ctx.multiplicativeExpr())

    def visitMultiplicativeExpr(self, ctx: CompiscriptParser.MultiplicativeExprContext):
        return self._binary_chain(ctx, ctx.unaryExpr())

    def visitUnaryExpr(self, ctx: CompiscriptParser.UnaryExprContext):
        if ctx.primaryExpr() is not None:
            return self.visit(ctx.primaryExpr())
        op = ctx.getChild(0).getText()
        value = self.expr(ctx.unaryExpr())
        if op == "-" and _NUM_LITERAL.fullmatch(value):
            # `-5` es una constante, no una operación.
            return value[1:] if value.startswith("-") else "-" + value
        self.e.free(value)
        t = self.e.new_temp()
        self.e.emit(f"{t} = {op} {value}")
        return t
