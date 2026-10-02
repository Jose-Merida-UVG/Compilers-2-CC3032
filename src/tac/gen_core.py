"""CoreMixin: TAC para declaraciones, asignaciones, expresiones y print.

Reglas de la gramática que implementa (ver docs/proyecto2/00-contrato.md
§4.1): variableDeclaration, constantDeclaration, assignment,
expressionStatement, printStatement, AssignExpr, literalExpr, primaryExpr,
IdentifierExpr, additiveExpr, multiplicativeExpr, unaryExpr, relationalExpr,
equalityExpr, logicalOrExpr, logicalAndExpr, TernaryExpr, gen_cond,
arrayLiteral e IndexExpr (más gen_index_load/gen_index_store/gen_len).

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
5. `gen_cond(ctx, ltrue, lfalse, fall=None)`: `fall` es opcional (la
   etiqueta que el llamador coloca justo después; evita un `goto`
   redundante). La versión por defecto de `gen_cond` del esqueleto debe
   vivir en una clase base listada DESPUÉS de los mixins
   (`class TACGenerator(CoreMixin, ..., BaseGen, CompiscriptVisitor)`);
   si se define en `TACGenerator` mismo tapa a la de este mixin.
6. Arreglos: `visitIndexExpr` devuelve solo el operando del ÍNDICE. La
   cadena `leftHandSide` (Tono) debe hacer, por cada sufijo `[ ]`,
   `base = self.gen_index_load(base, self.visit(sufijo))`. Para destinos
   de asignación con llamadas/propiedades antes del último sufijo
   (`obj.items[i] = v`), este mixin llama a `self.eval_chain(lhs, n)`:
   Tono lo expone (evalúa `primaryAtom` y los primeros `n` sufijos).
7. `visitAssignExpr` y `visitAssignment` no tocan temporales ajenos:
   devuelven la variable asignada (no es temporal, `free` es no-op).
"""

from __future__ import annotations

import re
from typing import Optional

from CompiscriptParser import CompiscriptParser

from semantic.types import ArrayType, BooleanType, FloatType, IntegerType, StringType, Type

_INT_LITERAL = re.compile(r"-?\d+")
_NUM_LITERAL = re.compile(r"-?\d+(\.\d+)?")

# Operador relacional con el resultado contrario: `if a < b` salta al
# else con `if a >= b`. Solo se usa para eliminar un `goto` redundante
# (ver gen_cond).
_NEGATED = {"<": ">=", "<=": ">", ">": "<=", ">=": "<", "==": "!=", "!=": "=="}


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
        if op in _NEGATED:
            return BooleanType()
        if isinstance(lt, FloatType) or isinstance(rt, FloatType):
            return FloatType()
        if isinstance(lt, StringType) or isinstance(rt, StringType):
            return StringType()
        return lt

    def _promote_pair(self, left: str, ltype, right: str, rtype):
        """integer mezclado con float: el entero se promueve."""
        if isinstance(ltype, FloatType) and isinstance(rtype, IntegerType):
            right = self._coerce(right, rtype, ltype)
        elif isinstance(rtype, FloatType) and isinstance(ltype, IntegerType):
            left = self._coerce(left, ltype, rtype)
        return left, right

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
            left, right = self._promote_pair(left, ltype, right, rtype)
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
        """`lhs = rhs` como expresión. Tres tipos de destino:
        `x = v` (variable), `a[i] = v` (arreglo) y `o.f = v` (campo).
        Devuelve el valor asignado (el llamador libera si es temporal)."""
        lhs = ctx.lhs
        suffixes = lhs.suffixOp()
        if not suffixes:
            value = self.expr(ctx.assignmentExpr())
            name = self._ident(lhs, lhs.primaryAtom().getText())
            symbol = self.symbol_of(lhs)
            value = self._coerce(
                value,
                self.type_of(ctx.assignmentExpr()),
                symbol.type if symbol is not None else None,
            )
            self.e.emit(f"{name} = {value}")
            self.e.free(value)
            return name  # variable, no temporal

        # Primero el destino (base e índice), luego el valor: así
        # `a[f()] = g()` evalúa en el orden en que se lee.
        last = suffixes[-1]
        base = self._eval_prefix(lhs, len(suffixes) - 1)
        if isinstance(last, CompiscriptParser.IndexExprContext):
            index = self.visit(last)
            value = self._rhs_for(ctx, lhs)
            self.gen_index_store(base, index, value)
            return value
        if isinstance(last, CompiscriptParser.PropertyAccessExprContext):
            value = self._rhs_for(ctx, lhs)
            self.e.emit(f"{base}.{last.Identifier().getText()} = {value}")
            self.e.free(base)
            return value
        raise NotImplementedError("el destino de una asignación no puede ser una llamada")

    def _rhs_for(self, ctx, lhs) -> str:
        """Valor de la derecha, promovido al tipo del destino."""
        value = self.expr(ctx.assignmentExpr())
        return self._coerce(value, self.type_of(ctx.assignmentExpr()), self.type_of(lhs))

    def _eval_prefix(self, lhs, count: int) -> str:
        """Valor de `primaryAtom` más los primeros `count` sufijos de una
        cadena. Si son todos índices (`m[i][j]`) se resuelve aquí; si hay
        llamadas o propiedades en medio se delega en `eval_chain` (Tono,
        dueño de la cadena `leftHandSide`)."""
        prefix = lhs.suffixOp()[:count]
        if all(isinstance(sf, CompiscriptParser.IndexExprContext) for sf in prefix):
            base = self.visit(lhs.primaryAtom())
            for sf in prefix:
                base = self.gen_index_load(base, self.visit(sf))
            return base
        return self.eval_chain(lhs, count)

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
        if op == "!" and value in ("true", "false"):
            return "false" if value == "true" else "true"
        self.e.free(value)
        t = self.e.new_temp()
        self.e.emit(f"{t} = {op} {value}")
        return t

    # ── Lógicas y comparaciones ─────────────────────────────────────────
    # Como *valor* (`let b = x < y;`) las comparaciones son una sola
    # instrucción `t = a < b`; `&&`/`||` se materializan con saltos
    # (cortocircuito) en `_materialize`. Como *condición* (if/while/...)
    # todo pasa por `gen_cond`, que nunca construye el booleano.
    def visitRelationalExpr(self, ctx: CompiscriptParser.RelationalExprContext):
        return self._binary_chain(ctx, ctx.additiveExpr())

    def visitEqualityExpr(self, ctx: CompiscriptParser.EqualityExprContext):
        return self._binary_chain(ctx, ctx.relationalExpr())

    def visitLogicalOrExpr(self, ctx: CompiscriptParser.LogicalOrExprContext):
        if len(ctx.logicalAndExpr()) == 1:
            return self.expr(ctx.logicalAndExpr(0))
        return self._materialize(ctx)

    def visitLogicalAndExpr(self, ctx: CompiscriptParser.LogicalAndExprContext):
        if len(ctx.equalityExpr()) == 1:
            return self.expr(ctx.equalityExpr(0))
        return self._materialize(ctx)

    def _materialize(self, ctx) -> str:
        """Condición compuesta usada como valor: salta a una de dos
        asignaciones (`t = true` / `t = false`). El temporal se pide
        *después* de gen_cond, que ya liberó los suyos."""
        ltrue, lfalse, lend = (self.e.new_label() for _ in range(3))
        self.gen_cond(ctx, ltrue, lfalse, fall=ltrue)
        t = self.e.new_temp()
        self._label_if_used(ltrue)
        self.e.emit(f"{t} = true")
        self._jump(lend, None)
        self._label_if_used(lfalse)
        self.e.emit(f"{t} = false")
        self.e.emit_label(lend)
        return t

    def visitTernaryExpr(self, ctx: CompiscriptParser.TernaryExprContext):
        branches = ctx.expression()
        if not branches:
            return self.expr(ctx.logicalOrExpr())  # no hay '?'
        ltrue, lfalse, lend = (self.e.new_label() for _ in range(3))
        self.gen_cond(ctx.logicalOrExpr(), ltrue, lfalse, fall=ltrue)
        # Las dos ramas escriben en el mismo temporal, pedido antes de
        # generarlas para que sus temporales internos no lo pisen.
        t = self.e.new_temp()
        result_type = self.type_of(ctx)
        self._label_if_used(ltrue)
        self._branch_value(t, branches[0], result_type)
        self._jump(lend, None)
        self._label_if_used(lfalse)
        self._branch_value(t, branches[1], result_type)
        self.e.emit_label(lend)
        return t

    def _branch_value(self, target: str, branch_ctx, result_type) -> None:
        value = self.expr(branch_ctx)
        value = self._coerce(value, self.type_of(branch_ctx), result_type)
        self.e.emit(f"{target} = {value}")
        self.e.free(value)

    # ── gen_cond: condiciones con saltos ────────────────────────────────
    _TRANSPARENT = {
        # contexto -> método que devuelve su único hijo cuando no hay operador
        "ExpressionContext": "assignmentExpr",
        "ExprNoAssignContext": "conditionalExpr",
    }

    def _strip(self, node):
        """Desciende por la cadena de precedencia mientras cada regla sea
        un simple paso (un solo operando, sin operador)."""
        P = CompiscriptParser
        while True:
            name = type(node).__name__
            if name in self._TRANSPARENT:
                node = getattr(node, self._TRANSPARENT[name])()
            elif isinstance(node, P.TernaryExprContext) and not node.expression():
                node = node.logicalOrExpr()
            elif isinstance(node, P.LogicalOrExprContext) and len(node.logicalAndExpr()) == 1:
                node = node.logicalAndExpr(0)
            elif isinstance(node, P.LogicalAndExprContext) and len(node.equalityExpr()) == 1:
                node = node.equalityExpr(0)
            elif isinstance(node, P.EqualityExprContext) and len(node.relationalExpr()) == 1:
                node = node.relationalExpr(0)
            elif isinstance(node, P.RelationalExprContext) and len(node.additiveExpr()) == 1:
                node = node.additiveExpr(0)
            elif isinstance(node, P.AdditiveExprContext) and len(node.multiplicativeExpr()) == 1:
                node = node.multiplicativeExpr(0)
            elif isinstance(node, P.MultiplicativeExprContext) and len(node.unaryExpr()) == 1:
                node = node.unaryExpr(0)
            elif isinstance(node, P.UnaryExprContext) and node.primaryExpr() is not None:
                node = node.primaryExpr()
            elif isinstance(node, P.PrimaryExprContext):
                if node.literalExpr() is not None:
                    node = node.literalExpr()
                elif node.leftHandSide() is not None:
                    return node.leftHandSide()
                else:
                    node = node.expression()  # '(' expression ')'
            else:
                return node

    # Etiquetas referenciadas por algún salto: `gen_cond` evita dejar
    # etiquetas muertas (`L4:` a las que nadie salta). Estado creado
    # perezosamente porque un mixin no tiene __init__.
    def _refs(self) -> set:
        if not hasattr(self, "_label_refs"):
            self._label_refs: set = set()
        return self._label_refs

    def _jump_to(self, instr: str, label: str) -> None:
        """Emite un salto (`goto L`, `if ... goto L`) y recuerda `L`."""
        self._refs().add(label)
        self.e.emit(f"{instr} {label}" if instr else f"goto {label}")

    def _label_if_used(self, label: str) -> None:
        """Coloca `label:` solo si algún salto lo referenció. Lo usan
        también los llamadores de gen_cond (control de flujo)."""
        if label in self._refs():
            self.e.emit_label(label)

    def _jump(self, label: str, fall: Optional[str]) -> None:
        if label != fall:
            self._jump_to("", label)

    def gen_cond(self, ctx, ltrue: str, lfalse: str, fall: Optional[str] = None) -> None:
        """Emite saltos: a `ltrue` si la condición es verdadera, a `lfalse`
        si no. `fall` es la etiqueta que el llamador colocará justo
        después; si coincide con una de las dos, ese salto se omite
        (`if a >= b goto Lf` y se cae en el cuerpo, en vez de
        `if a < b goto Lt` + `goto Lf`).

        `&&`/`||` se evalúan con cortocircuito; `!` intercambia las
        etiquetas. Nunca se materializa un booleano.
        """
        P = CompiscriptParser
        node = self._strip(ctx)

        if isinstance(node, P.LogicalOrExprContext):
            *init, last = node.logicalAndExpr()
            for operand in init:  # si es verdadero ya no se evalúa el resto
                lnext = self.e.new_label()
                self.gen_cond(operand, ltrue, lnext, fall=lnext)
                self._label_if_used(lnext)
            return self.gen_cond(last, ltrue, lfalse, fall)

        if isinstance(node, P.LogicalAndExprContext):
            *init, last = node.equalityExpr()
            for operand in init:  # si es falso ya no se evalúa el resto
                lnext = self.e.new_label()
                self.gen_cond(operand, lnext, lfalse, fall=lnext)
                self._label_if_used(lnext)
            return self.gen_cond(last, ltrue, lfalse, fall)

        if isinstance(node, P.UnaryExprContext) and node.getChild(0).getText() == "!":
            return self.gen_cond(node.unaryExpr(), lfalse, ltrue, fall)

        if isinstance(node, (P.RelationalExprContext, P.EqualityExprContext)):
            operands = (
                node.additiveExpr()
                if isinstance(node, P.RelationalExprContext)
                else node.relationalExpr()
            )
            if len(operands) == 2:
                op = node.getChild(1).getText()
                left = self.expr(operands[0])
                right = self.expr(operands[1])
                left, right = self._promote_pair(
                    left, self.type_of(operands[0]), right, self.type_of(operands[1])
                )
                self.e.free(left)
                self.e.free(right)
                if fall == ltrue:
                    self._jump_to(f"if {left} {_NEGATED[op]} {right} goto", lfalse)
                else:
                    self._jump_to(f"if {left} {op} {right} goto", ltrue)
                    self._jump(lfalse, fall)
                return None
            # a < b < c, a == b == c: caen al caso general (valor + salto)

        if isinstance(node, P.LiteralExprContext) and node.getText() in ("true", "false"):
            self._jump(ltrue if node.getText() == "true" else lfalse, fall)
            return None

        # General: un booleano ya calculado (variable, llamada, ...).
        value = self.expr(node)
        self.e.free(value)
        if fall == ltrue:
            self._jump_to(f"ifFalse {value} goto", lfalse)
        else:
            self._jump_to(f"if {value} goto", ltrue)
            self._jump(lfalse, fall)
        return None

    # ── Arreglos ────────────────────────────────────────────────────────
    def visitArrayLiteral(self, ctx: CompiscriptParser.ArrayLiteralContext):
        """`[e0, e1, ...]` -> `t = newarray n` y un `t[i] = ei` por
        elemento. El temporal del arreglo vive mientras se evalúan los
        elementos; cada elemento se promueve al tipo del arreglo
        (`[1, 2.5]` es float[])."""
        elements = ctx.expression()
        array_type = self.type_of(ctx)
        element_type = array_type.element if isinstance(array_type, ArrayType) else None
        t = self.e.new_temp()
        self.e.emit(f"{t} = newarray {len(elements)}")
        for i, element in enumerate(elements):
            value = self.expr(element)
            value = self._coerce(value, self.type_of(element), element_type)
            self.e.emit(f"{t}[{i}] = {value}")
            self.e.free(value)
        return t

    def visitIndexExpr(self, ctx: CompiscriptParser.IndexExprContext):
        # Solo evalúa el índice. La cadena `leftHandSide` (Tono) lleva la
        # base y llama a `gen_index_load(base, indice)`.
        return self.expr(ctx.expression())

    def gen_index_load(self, base: str, index: str) -> str:
        """`t = base[index]`; libera base e índice antes de pedir `t`."""
        self.e.free(base)
        self.e.free(index)
        t = self.e.new_temp()
        self.e.emit(f"{t} = {base}[{index}]")
        return t

    def gen_index_store(self, base: str, index: str, value: str) -> None:
        """`base[index] = value`; libera base e índice, NO el valor (es el
        resultado de la asignación y lo libera quien lo consuma)."""
        self.e.emit(f"{base}[{index}] = {value}")
        self.e.free(base)
        self.e.free(index)

    def gen_len(self, array: str) -> str:
        """`t = len array` (lo usa foreach)."""
        self.e.free(array)
        t = self.e.new_temp()
        self.e.emit(f"{t} = len {array}")
        return t
