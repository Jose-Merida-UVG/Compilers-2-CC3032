"""The semantic checker: one ANTLR Visitor that walks the parse tree built
by src/compiler.py and applies the rules from docs/plan-proyecto1.md.

Status: Fase 0 skeleton. `check()` runs end-to-end today and returns zero
errors -- every rule method below is a deliberate no-op (`visitChildren`,
identical to the inherited default) until its owner fills it in. This file
exists so the whole team is editing the *same* method names / scope
boundaries instead of three diverging designs.

Ownership follows docs/plan-proyecto1.md's division. A few rules
legitimately need input from two people (e.g. a function's parameter list
touches both "ámbito" and "funciones") -- noted inline where that happens;
whoever gets there first should still open the PR and tag the other.

Wiring: `compiler.py` calls `SemanticChecker().check(tree)` only when there
are no lexical/syntax errors (see decision in that file) -- walking a
parse tree ANTLR had to error-recover through is likely to produce noisy,
misleading semantic errors on top of real ones.
"""
from __future__ import annotations

from typing import Optional

from CompiscriptParser import CompiscriptParser
from CompiscriptVisitor import CompiscriptVisitor

from semantic.errors import SemanticErrorList
from semantic.symbols import ScopeKind, Symbol, SymbolKind, SymbolTable
from semantic.types import (
    ArrayType,
    BooleanType,
    ClassType,
    ErrorType,
    FloatType,
    FunctionType,
    IntegerType,
    NullType,
    PRIMITIVE_TYPES,
    StringType,
    Type,
    UnknownType,
    VoidType,
)

Ctx = object  # any ANTLR ParserRuleContext -- avoids importing every *Context class here


class SemanticChecker(CompiscriptVisitor):
    def __init__(self) -> None:
        self.symbols = SymbolTable()
        self.errors = SemanticErrorList()
        # Persona 2 state (funciones/llamadas) -- see visitFunctionDeclaration,
        # visitReturnStatement, visitLeftHandSide/visitCallExpr below for how
        # each is pushed/read/popped.
        self._function_return_stack: list[Type] = []
        self._chain_base: Optional[Type] = None

    def check(self, tree: Ctx) -> SemanticErrorList:
        self.visit(tree)
        return self.errors

    # ── helpers ──────────────────────────────────────────────────────────

    def _error(self, ctx: Ctx, message: str) -> None:
        """Record a semantic error anchored at the start token of `ctx`."""
        self.errors.add(ctx.start.line, ctx.start.column, message)

    def _resolve_type_node(self, type_ctx: CompiscriptParser.TypeContext) -> Type:
        """Resolve a `type` parse node (`baseType ('[' ']')*`) to a
        semantic Type. Shared helper -- not just Persona 1's concern:
        function params/return types (Persona 2) and array element types
        (Persona 3) need this exact same syntax -> Type mapping, so it
        lives here once instead of being reimplemented per rule."""
        base_name = type_ctx.baseType().getText()
        result: Type = PRIMITIVE_TYPES.get(base_name)
        if result is None:
            # Not a primitive -> grammar's only other baseType alternative
            # is a bare Identifier, i.e. a class name.
            # TODO: validate the class was actually declared once class
            # registration exists (visitClassDeclaration) -- for now this
            # trusts the name and builds a ClassType regardless.
            result = ClassType(base_name)
        # `('[' ']')*` -- each '[' ']' pair adds one array dimension.
        array_dims = (type_ctx.getChildCount() - 1) // 2
        for _ in range(array_dims):
            result = ArrayType(result)
        return result

    def _visit_type(self, ctx: Ctx) -> Type:
        """self.visit(ctx) on an expression is expected to yield a Type,
        but a still-unimplemented Persona 3 rule (arrays, `new`, index/
        property access) currently falls through to ANTLR's default
        visitChildren and returns plain None instead of ErrorType. Every
        Persona 2 method that immediately calls `.is_assignable_to(...)`
        or similar on a freshly-visited value goes through this instead
        of raw `self.visit(...)`, so that gap can't crash the checker --
        treat None the same as ErrorType (already-covered territory,
        don't cascade a second error)."""
        result = self.visit(ctx)
        return result if result is not None else ErrorType()

    @staticmethod
    def _is_numeric(t: Type) -> bool:
        return isinstance(t, (IntegerType, FloatType))

    @staticmethod
    def _operator_before(ctx: Ctx, i: int) -> str:
        """Text of the operator token immediately before the i-th operand
        (i >= 1) of a left-associative `sub (OP sub)*` rule -- children
        alternate operand, operator, operand, operator, ..., so the
        operator sits at index 2*i-1. Shared by every binary-expression
        rule in Persona 2's section below (additive, multiplicative,
        relational, equality, logical)."""
        return ctx.getChild(2 * i - 1).getText()

    # ── Persona 1: Tabla de Símbolos + Ámbito ───────────────────────────
    # declare/resolve via self.symbols (SymbolTable, see symbols.py);
    # push/pop scopes with self.symbols.enter_scope(...)/.exit_scope().

    def visitBlock(self, ctx: CompiscriptParser.BlockContext):
        # New lexical scope per block. try/finally guarantees exit_scope()
        # runs even if a statement inside raises/errors out mid-visit, so
        # a bad block never leaves the scope stack unbalanced for the rest
        # of the walk (see SymbolTable.exit_scope's docstring).
        #
        # Note for Persona 3: "código muerto" (statements after
        # return/break/continue) is naturally detected right here, by
        # noticing such a statement isn't the last child visited.
        self.symbols.enter_scope(ScopeKind.BLOCK)
        try:
            return self.visitChildren(ctx)
        finally:
            self.symbols.exit_scope()

    def visitVariableDeclaration(self, ctx: CompiscriptParser.VariableDeclarationContext):
            # 'let' and 'var' are two syntactic spellings of the same thing in
            # this grammar (no separate SymbolKind for each) -- both declare a
            # SymbolKind.VARIABLE.
            name = ctx.Identifier().getText()

            if ctx.typeAnnotation():
                declared_type: Type = self._resolve_type_node(ctx.typeAnnotation().type_())
            else:
                # Coordination with Persona 2 resolved: narrowed from the
                # initializer's type below (same mechanism as an
                # UnknownType symbol's first assignment) once expression
                # visiting exists. Stays UnknownType for `let x;` with no
                # initializer at all.
                declared_type = UnknownType()

            symbol = Symbol(
                name=name,
                kind=SymbolKind.VARIABLE,
                type=declared_type,
                line=ctx.start.line,
                column=ctx.start.column,
            )
            if not self.symbols.declare(symbol):
                self._error(ctx, f"la variable '{name}' ya fue declarada en este ámbito")

            # Declared *before* walking the initializer: `let x = x + 1;`
            # resolves the rhs `x` to this new declaration rather than
            # erroring as undeclared. Whether that should instead be a "used
            # before initialized" error is an open question -- flag it to the
            # team if a test case makes it matter.
            if ctx.initializer():
                value_type = self._visit_type(ctx.initializer().expression())
                if not isinstance(value_type, ErrorType):
                    if isinstance(symbol.type, UnknownType):
                        symbol.type = value_type  # no annotation -- infer, for good
                    elif not value_type.is_assignable_to(symbol.type):
                        self._error(
                            ctx,
                            f"la variable '{name}' se declaró como {symbol.type} "
                            f"pero se inicializa con un valor de tipo {value_type}",
                        )
                return None
            return self.visitChildren(ctx)

    def visitClassDeclaration(self, ctx: CompiscriptParser.ClassDeclarationContext):
        # `'class' Identifier (':' Identifier)? '{' classMember* '}'` --
        # both the class name and the optional parent name are plain
        # Identifier tokens on this same (unlabeled) context, in source
        # order: index 0 is always the class's own name; index 1, if
        # present, is the parent's name.
        identifiers = ctx.Identifier()
        class_name = identifiers[0].getText()
 
        parent_type: Optional[ClassType] = None
        if len(identifiers) > 1:
            parent_name = identifiers[1].getText()
            parent_symbol = self.symbols.resolve(parent_name)
            if parent_symbol is None or parent_symbol.kind is not SymbolKind.CLASS:
                self._error(ctx, f"la clase base '{parent_name}' no ha sido declarada")
            elif isinstance(parent_symbol.type, ClassType):
                parent_type = parent_symbol.type
 
        class_type = ClassType(class_name, parent=parent_type)
        symbol = Symbol(
            name=class_name,
            kind=SymbolKind.CLASS,
            type=class_type,
            line=ctx.start.line,
            column=ctx.start.column,
        )
        if not self.symbols.declare(symbol):
            self._error(ctx, f"la clase '{class_name}' ya fue declarada en este ámbito")
 
        # New scope for the class body: this is what makes members declare
        # into their own namespace instead of leaking into whatever scope
        # contains the class declaration -- that leak was exactly the
        # false "ya fue declarada" collision seen before this method
        # existed (a top-level `let nombre` colliding with a class's own
        # `var nombre` member, since classMember visits fell straight
        # through to visitVariableDeclaration with no scope in between).
        # Persona 3 needs this same CLASS-kind scope for '.' access and
        # `this` (Scope.enclosing(ScopeKind.CLASS)).
        self.symbols.enter_scope(ScopeKind.CLASS)
        try:
            return self.visitChildren(ctx)
        finally:
            self.symbols.exit_scope()

    def visitIdentifierExpr(self, ctx: CompiscriptParser.IdentifierExprContext):
        # Read-side counterpart to visitVariableDeclaration: resolve walks
        # up through parent scopes (see Scope.resolve), so this also
        # covers reading a variable from an enclosing function/block --
        # closures fall out of this for free, no special-casing needed.
        name = ctx.Identifier().getText()
        symbol = self.symbols.resolve(name)
        if symbol is None:
            self._error(ctx, f"la variable '{name}' no ha sido declarada")
            # ErrorType, not UnknownType: this *is* the error being
            # reported, not a legitimately-unresolved-yet type -- returning
            # ErrorType stops it from cascading into unrelated errors in
            # whatever expression contains this identifier (see
            # types.py's ErrorType docstring).
            return ErrorType()
        return symbol.type

    def visitAssignment(self, ctx: CompiscriptParser.AssignmentContext):
        # This is the statement-level rule (`Identifier '=' expression ';'`
        # or the property-assignment alternative), NOT visitAssignExpr
        # below -- `statement` tries `assignment` before
        # `expressionStatement`, so a plain `x = 5;` always parses through
        # *this* method. visitAssignExpr (Persona 2) only fires when an
        # assignment shows up nested inside a larger expression (e.g.
        # `print(x = 5)`), which is rare in practice.
        #
        # Both alternatives share this same (unlabeled) context class, so
        # ctx.Identifier() alone can't tell them apart -- ctx.expression()
        # returns 1 item for the plain form (just the rhs) and 2 for the
        # property form (target object + rhs), which is how we tell them
        # apart below.
        exprs = ctx.expression()
        if len(exprs) == 1:
            # Plain form: Identifier '=' expression ';'
            name = ctx.Identifier().getText()
            symbol = self.symbols.resolve(name)
            rhs_type = self._visit_type(exprs[0])

            if symbol is None:
                self._error(ctx, f"la variable '{name}' no ha sido declarada")
                return None
            if isinstance(rhs_type, ErrorType):
                return None
            if isinstance(symbol.type, UnknownType):
                # Coordination with Persona 2 resolved: first assignment
                # narrows an UnknownType symbol, for good -- same
                # mechanism as visitAssignExpr.
                symbol.type = rhs_type
            elif not rhs_type.is_assignable_to(symbol.type):
                self._error(
                    ctx,
                    f"no se puede asignar un valor de tipo {rhs_type} a una variable de tipo {symbol.type}",
                )
            return None
 
        # Property form: expression '.' Identifier '=' expression ';'
        # (e.g. `obj.campo = valor;`). Validating that the property
        # actually exists on the target's ClassType is Persona 3's '.'
        # access work (visitPropertyAccessExpr) -- this just walks both
        # expression subtrees so nested identifiers etc. still get
        # visited. Whoever implements the property check first should tag
        # the other.
        return self.visitChildren(ctx)

    def visitForeachStatement(self, ctx: CompiscriptParser.ForeachStatementContext):
        # 'foreach' '(' Identifier 'in' expression ')' block
        name = ctx.Identifier().getText()
 
        # Visited directly (not via visitChildren) so we can inspect its
        # resolved type before deciding the loop variable's type, and so
        # it isn't visited a second time when we walk the block below.
        iterated_type = self.visit(ctx.expression())
 
        if iterated_type is None:
            # Some part of the type-inference chain for this expression
            # isn't implemented yet (e.g. array literals -- Persona 3 --
            # or call expressions -- Persona 2), so we genuinely don't
            # know yet. Stay silent rather than raise a false "no es un
            # arreglo" error; this should stop happening on its own as
            # those rules land.
            element_type: Type = UnknownType()
        elif isinstance(iterated_type, ArrayType):
            element_type = iterated_type.element
        elif isinstance(iterated_type, ErrorType):
            # Don't cascade: whatever produced this ErrorType already
            # reported its own error.
            element_type = ErrorType()
        else:
            self._error(ctx, "la expresión de 'foreach' debe ser un arreglo")
            element_type = ErrorType()
 
        # New BLOCK scope for the body, same shape as visitBlock: the loop
        # variable lives only inside it, with the array's element type.
        # Persona 3 needs this same scope to exist so foreach bodies
        # support break/continue like other loops (their loop-tracking
        # counter should increment here too).
        self.symbols.enter_scope(ScopeKind.BLOCK)
        try:
            self.symbols.declare(
                Symbol(
                    name=name,
                    kind=SymbolKind.VARIABLE,
                    type=element_type,
                    line=ctx.start.line,
                    column=ctx.start.column,
                )
            )
            return self.visit(ctx.block())
        finally:
            self.symbols.exit_scope()

    def visitTryCatchStatement(self, ctx: CompiscriptParser.TryCatchStatementContext):
        # OUT OF SCOPE (team decision): this wasn't in
        # docs/plan-proyecto1.md's division, and the team decided not to
        # add semantic checking for try/catch for this project. Left as a
        # plain passthrough on purpose -- not a forgotten TODO.
        return self.visitChildren(ctx)

    # ── Persona 2: Sistema de Tipos + Funciones ─────────────────────────
    #
    # visitLiteralExpr/visitPrimaryExpr/visitLeftHandSide below weren't
    # anyone's TODO in the Fase 0 skeleton, but the rest of this section
    # can't produce a real Type without them (literals are the base case
    # of every expression, and the default ANTLR visitChildren aggregation
    # silently returns None for a parenthesized `(expr)` and can't thread
    # a call's callee type into visitCallExpr at all) -- claiming them
    # here since "sistema de tipos" is this section's whole job.

    def visitLiteralExpr(self, ctx: CompiscriptParser.LiteralExprContext):
        # literalExpr: Literal | arrayLiteral | 'null' | 'true' | 'false';
        # NOTE: the grammar's `Literal` lexer rule is declared *before*
        # FloatLiteral/IntegerLiteral/StringLiteral and matches the exact
        # same spans as all three -- ANTLR's earliest-rule tiebreak means
        # every numeric/string literal actually lexes as token type
        # `Literal`, never as the more specific ones (verified against the
        # generated lexer). So the specific kind has to be sniffed from
        # the literal's own text here instead of from the token type.
        if ctx.Literal() is not None:
            text = ctx.Literal().getText()
            if text.startswith('"'):
                return StringType()
            if '.' in text:
                return FloatType()
            return IntegerType()
        if ctx.arrayLiteral() is not None:
            # Persona 3's rule (arreglos) -- passthrough for whatever it
            # eventually returns; _visit_type maps its still-unimplemented
            # None to ErrorType so callers don't have to special-case it.
            return self._visit_type(ctx.arrayLiteral())
        text = ctx.getText()
        if text == "null":
            return NullType()
        # Only remaining grammar alternative is 'true' | 'false'.
        return BooleanType()

    def visitPrimaryExpr(self, ctx: CompiscriptParser.PrimaryExprContext):
        # primaryExpr: literalExpr | leftHandSide | '(' expression ')';
        # Needs an explicit override: for the parenthesized alternative,
        # ANTLR's default child-aggregation would return the *last*
        # child's result, i.e. the closing ')' terminal -- None, not the
        # inner expression's type.
        if ctx.literalExpr() is not None:
            return self._visit_type(ctx.literalExpr())
        if ctx.leftHandSide() is not None:
            return self._visit_type(ctx.leftHandSide())
        return self._visit_type(ctx.expression())

    def visitLeftHandSide(self, ctx: CompiscriptParser.LeftHandSideContext):
        # leftHandSide: primaryAtom (suffixOp)*; -- e.g. `foo`, `foo(1,2)`,
        # `obj.campo`, `arr[0]`, or a chain like `obj.metodo(1).campo`.
        # Each suffixOp needs the type of *what came before it in the
        # chain* (the callee for a call, the array for an index, the
        # object for a property access) -- that's not available from the
        # suffixOp's own ctx, so it's threaded through `self._chain_base`
        # right before visiting each one.
        #
        # For Persona 3 (visitIndexExpr/visitPropertyAccessExpr/
        # visitNewExpr/visitThisExpr): read `self._chain_base` immediately
        # at the top of your method, before visiting any nested subtree
        # (e.g. an index expression) that could itself be a chain and
        # overwrite it before you've read it.
        current: Type = self._visit_type(ctx.primaryAtom())
        for suffix in ctx.suffixOp():
            self._chain_base = current
            current = self._visit_type(suffix)
        return current

    def visitConstantDeclaration(self, ctx: CompiscriptParser.ConstantDeclarationContext):
        # constantDeclaration: 'const' Identifier typeAnnotation? '=' expression ';'
        # The grammar already makes the initializer mandatory (it's not
        # `initializer?` like variableDeclaration, just a bare
        # '=' expression), so "const must be initialized" falls out for
        # free -- this is really just declare + type-check, mirroring
        # visitVariableDeclaration's shape (Persona 1) but for CONSTANT
        # and with no UnknownType branch: a const's type is settled here,
        # for good, since it can never be reassigned afterward.
        name = ctx.Identifier().getText()
        value_type = self._visit_type(ctx.expression())

        if ctx.typeAnnotation():
            declared_type = self._resolve_type_node(ctx.typeAnnotation().type_())
            if not isinstance(value_type, ErrorType) and not value_type.is_assignable_to(declared_type):
                self._error(
                    ctx,
                    f"la constante '{name}' se declaró como {declared_type} "
                    f"pero se inicializa con un valor de tipo {value_type}",
                )
            symbol_type: Type = declared_type
        else:
            symbol_type = ErrorType() if isinstance(value_type, ErrorType) else value_type

        symbol = Symbol(
            name=name,
            kind=SymbolKind.CONSTANT,
            type=symbol_type,
            line=ctx.start.line,
            column=ctx.start.column,
        )
        if not self.symbols.declare(symbol):
            self._error(ctx, f"'{name}' ya fue declarada en este ámbito")
        return None

    def visitAdditiveExpr(self, ctx: CompiscriptParser.AdditiveExprContext):
        operands = ctx.multiplicativeExpr()
        result: Type = self._visit_type(operands[0])
        for i in range(1, len(operands)):
            op = self._operator_before(ctx, i)
            rhs = self._visit_type(operands[i])
            result = self._check_additive(ctx, op, result, rhs)
        return result

    def _check_additive(self, ctx: Ctx, op: str, left: Type, right: Type) -> Type:
        if isinstance(left, ErrorType) or isinstance(right, ErrorType):
            return ErrorType()
        # '+' doubles as string concatenation -- required by the
        # language's own spec example (`return "Hola " + nombre;` in
        # docs/DefinicionCompiscript.md), so this isn't purely numeric
        # like '-' is.
        if op == "+" and isinstance(left, StringType) and isinstance(right, StringType):
            return StringType()
        if self._is_numeric(left) and self._is_numeric(right):
            return FloatType() if isinstance(left, FloatType) or isinstance(right, FloatType) else IntegerType()
        expected = "integer, float, o string (solo para '+')" if op == "+" else "integer o float"
        self._error(ctx, f"el operador '{op}' requiere operandos de tipo {expected}; se encontró {left} y {right}")
        return ErrorType()

    def visitMultiplicativeExpr(self, ctx: CompiscriptParser.MultiplicativeExprContext):
        operands = ctx.unaryExpr()
        result: Type = self._visit_type(operands[0])
        for i in range(1, len(operands)):
            op = self._operator_before(ctx, i)
            rhs = self._visit_type(operands[i])
            if isinstance(result, ErrorType) or isinstance(rhs, ErrorType):
                result = ErrorType()
            elif self._is_numeric(result) and self._is_numeric(rhs):
                result = FloatType() if isinstance(result, FloatType) or isinstance(rhs, FloatType) else IntegerType()
            else:
                self._error(ctx, f"el operador '{op}' requiere operandos de tipo integer o float; se encontró {result} y {rhs}")
                result = ErrorType()
        return result

    def visitUnaryExpr(self, ctx: CompiscriptParser.UnaryExprContext):
        # unaryExpr: ('-' | '!') unaryExpr | primaryExpr;
        if ctx.primaryExpr() is not None:
            return self._visit_type(ctx.primaryExpr())

        op = ctx.getChild(0).getText()
        operand = self._visit_type(ctx.unaryExpr())
        if isinstance(operand, ErrorType):
            return ErrorType()
        if op == "!":
            if not isinstance(operand, BooleanType):
                self._error(ctx, f"el operador '!' requiere un operando de tipo boolean; se encontró {operand}")
                return ErrorType()
            return BooleanType()
        # op == '-'
        if not self._is_numeric(operand):
            self._error(ctx, f"el operador unario '-' requiere un operando de tipo integer o float; se encontró {operand}")
            return ErrorType()
        return operand

    def visitTernaryExpr(self, ctx: CompiscriptParser.TernaryExprContext):
        # conditionalExpr: logicalOrExpr ('?' expression ':' expression)? # TernaryExpr;
        cond = self._visit_type(ctx.logicalOrExpr())
        branches = ctx.expression()
        if not branches:
            return cond  # no '?' present -- plain passthrough

        if not isinstance(cond, (ErrorType, BooleanType)):
            self._error(ctx, f"la condición del operador ternario debe ser boolean; se encontró {cond}")

        then_type = self._visit_type(branches[0])
        else_type = self._visit_type(branches[1])
        if isinstance(then_type, ErrorType) or isinstance(else_type, ErrorType):
            return ErrorType()
        if then_type.is_assignable_to(else_type):
            return else_type
        if else_type.is_assignable_to(then_type):
            return then_type
        self._error(
            ctx,
            f"las dos ramas del operador ternario deben tener tipos compatibles; "
            f"se encontró {then_type} y {else_type}",
        )
        return ErrorType()

    def visitLogicalOrExpr(self, ctx: CompiscriptParser.LogicalOrExprContext):
        return self._check_logical(ctx, ctx.logicalAndExpr(), "||")

    def visitLogicalAndExpr(self, ctx: CompiscriptParser.LogicalAndExprContext):
        return self._check_logical(ctx, ctx.equalityExpr(), "&&")

    def _check_logical(self, ctx: Ctx, operands, op: str) -> Type:
        # `sub (OP sub)*`: with a single operand (no OP actually present),
        # this rule is a transparent link in the expression precedence
        # chain -- EVERY expression flows through logicalOrExpr/
        # logicalAndExpr on its way down to a literal, not just genuinely
        # boolean ones, so the single-operand case must pass the real
        # type through unchanged rather than coercing it to boolean.
        result = self._visit_type(operands[0])
        if len(operands) == 1:
            return result
        ok = True
        if isinstance(result, ErrorType):
            ok = False
        elif not isinstance(result, BooleanType):
            self._error(ctx, f"el operador '{op}' requiere operandos de tipo boolean; se encontró {result}")
            ok = False
        for operand_ctx in operands[1:]:
            t = self._visit_type(operand_ctx)
            if isinstance(t, ErrorType):
                ok = False
            elif not isinstance(t, BooleanType):
                self._error(ctx, f"el operador '{op}' requiere operandos de tipo boolean; se encontró {t}")
                ok = False
        return BooleanType() if ok else ErrorType()

    def visitEqualityExpr(self, ctx: CompiscriptParser.EqualityExprContext):
        # Same passthrough note as _check_logical above: with a single
        # operand (no '=='/'!=' present) this must return the real type,
        # not force BooleanType.
        operands = ctx.relationalExpr()
        result: Type = self._visit_type(operands[0])
        if len(operands) == 1:
            return result
        ok = not isinstance(result, ErrorType)
        for i in range(1, len(operands)):
            op = self._operator_before(ctx, i)
            rhs = self._visit_type(operands[i])
            if isinstance(rhs, ErrorType):
                ok = False
            elif not (result.is_assignable_to(rhs) or rhs.is_assignable_to(result)):
                self._error(ctx, f"el operador '{op}' requiere operandos de tipos compatibles; se encontró {result} y {rhs}")
                ok = False
            result = rhs
        return BooleanType() if ok else ErrorType()

    def visitRelationalExpr(self, ctx: CompiscriptParser.RelationalExprContext):
        # Same passthrough note as _check_logical above: with a single
        # operand (no '<'/'<='/'>'/'>=' present) this must return the real
        # type, not force BooleanType.
        operands = ctx.additiveExpr()
        result: Type = self._visit_type(operands[0])
        if len(operands) == 1:
            return result
        ok = not isinstance(result, ErrorType)
        for i in range(1, len(operands)):
            op = self._operator_before(ctx, i)
            rhs = self._visit_type(operands[i])
            if isinstance(rhs, ErrorType):
                ok = False
            elif not (self._is_numeric(result) and self._is_numeric(rhs)):
                self._error(ctx, f"el operador '{op}' requiere operandos de tipo integer o float; se encontró {result} y {rhs}")
                ok = False
            result = rhs
        return BooleanType() if ok else ErrorType()

    def _resolve_assignment_target(self, lhs_ctx: CompiscriptParser.LeftHandSideContext):
        """For a bare-identifier lhs (`x = ...`, no suffixOp), return
        (symbol, its current type) so UnknownType can be narrowed in
        visitAssignExpr on first assignment. For anything with suffixOps
        (`arr[0] = ...`, `obj.campo = ...` reached through here, chains --
        there's no single Symbol to narrow for those), return
        (None, the visited type) for a plain compatibility check instead."""
        if len(lhs_ctx.suffixOp()) == 0:
            name = lhs_ctx.primaryAtom().getText()
            symbol = self.symbols.resolve(name)
            if symbol is None:
                self._error(lhs_ctx, f"la variable '{name}' no ha sido declarada")
                return None, ErrorType()
            return symbol, symbol.type
        return None, self._visit_type(lhs_ctx)

    def visitAssignExpr(self, ctx: CompiscriptParser.AssignExprContext):
        # assignmentExpr: lhs=leftHandSide '=' assignmentExpr # AssignExpr;
        # This is the general form -- lhs can be a bare identifier *or* a
        # chain like `arr[0]` (leftHandSide allows suffixOps), so it
        # covers more than just "assignment nested in a larger expression"
        # (e.g. `print(x = 5)`): `arr[0] = 5;` as a standalone statement
        # also parses through here via expressionStatement, since it
        # doesn't match the statement-level `assignment` rule's two
        # simpler alternatives (see visitAssignment's comment, Persona 1).
        rhs_type = self._visit_type(ctx.assignmentExpr())
        symbol, target_type = self._resolve_assignment_target(ctx.lhs)

        if isinstance(rhs_type, ErrorType) or isinstance(target_type, ErrorType):
            return ErrorType()

        if symbol is not None and isinstance(symbol.type, UnknownType):
            symbol.type = rhs_type  # first assignment narrows it, for good
            return rhs_type

        if not rhs_type.is_assignable_to(target_type):
            self._error(ctx, f"no se puede asignar un valor de tipo {rhs_type} a una variable de tipo {target_type}")
            return ErrorType()
        return target_type

    def visitFunctionDeclaration(self, ctx: CompiscriptParser.FunctionDeclarationContext):
        # functionDeclaration: 'function' Identifier '(' parameters? ')' (':' type)? block;
        name = ctx.Identifier().getText()

        param_names: list[str] = []
        param_types: list[Type] = []
        if ctx.parameters():
            for param_ctx in ctx.parameters().parameter():
                param_names.append(param_ctx.Identifier().getText())
                if param_ctx.type_():
                    param_types.append(self._resolve_type_node(param_ctx.type_()))
                else:
                    # Untyped parameter: accepts any argument (see
                    # UnknownType.is_assignable_to / the target-side
                    # UnknownType case added to Type.is_assignable_to in
                    # types.py for this exact case).
                    param_types.append(UnknownType())

        return_type: Type = self._resolve_type_node(ctx.type_()) if ctx.type_() else VoidType()
        function_type = FunctionType(param_types, return_type)

        symbol = Symbol(
            name=name,
            kind=SymbolKind.FUNCTION,
            type=function_type,
            line=ctx.start.line,
            column=ctx.start.column,
        )
        # Declared in the *enclosing* scope, before entering the
        # function's own scope below: that's what makes a recursive call
        # inside the body resolve (it walks up through the function scope
        # to find its own name here), and what lets the function be
        # called from outside afterward. Redeclaring a name here is the
        # "sin sobrecarga" rule from docs/plan-proyecto1.md.
        if not self.symbols.declare(symbol):
            self._error(ctx, f"la función '{name}' ya fue declarada en este ámbito (no se soporta sobrecarga)")

        self.symbols.enter_scope(ScopeKind.FUNCTION)
        self._function_return_stack.append(return_type)
        try:
            for param_name, param_type in zip(param_names, param_types):
                param_symbol = Symbol(
                    name=param_name,
                    kind=SymbolKind.PARAMETER,
                    type=param_type,
                    line=ctx.start.line,
                    column=ctx.start.column,
                )
                if not self.symbols.declare(param_symbol):
                    self._error(ctx, f"el parámetro '{param_name}' está duplicado")
            # Nested functions (closures): visiting the block here means a
            # `function` declared inside this body runs this same method
            # again, declaring the inner function into *this* FUNCTION
            # scope (self.symbols.current at that point) -- its own body
            # then chains up through here for outer locals/parameters, so
            # closures fall out for free with no special-casing.
            self.visit(ctx.block())
        finally:
            self._function_return_stack.pop()
            self.symbols.exit_scope()
        return None

    def visitCallExpr(self, ctx: CompiscriptParser.CallExprContext):
        # suffixOp: '(' arguments? ')' # CallExpr; -- only ever reached as
        # a suffixOp of leftHandSide, which stashes the callee's type in
        # self._chain_base right before visiting this (see
        # visitLeftHandSide). Read it before visiting the arguments below:
        # they can themselves contain a call/chain that would overwrite
        # self._chain_base before we're done with it.
        callee_type = self._chain_base

        arg_exprs = ctx.arguments().expression() if ctx.arguments() else []
        arg_types = [self._visit_type(a) for a in arg_exprs]

        if callee_type is None or isinstance(callee_type, ErrorType):
            return ErrorType()
        if not isinstance(callee_type, FunctionType):
            self._error(ctx, f"solo se puede invocar una función; se encontró {callee_type}")
            return ErrorType()

        if len(arg_types) != len(callee_type.params):
            self._error(
                ctx,
                f"se esperaban {len(callee_type.params)} argumento(s) y se recibieron {len(arg_types)}",
            )
            return ErrorType()

        ok = True
        for i, (arg_type, param_type) in enumerate(zip(arg_types, callee_type.params), start=1):
            if isinstance(arg_type, ErrorType):
                ok = False
            elif not arg_type.is_assignable_to(param_type):
                self._error(ctx, f"el argumento {i} debe ser de tipo {param_type}; se encontró {arg_type}")
                ok = False
        return callee_type.ret if ok else ErrorType()

    def visitReturnStatement(self, ctx: CompiscriptParser.ReturnStatementContext):
        # "return solo dentro de una función" is Persona 3's rule (control
        # de flujo) -- this guard just avoids an IndexError until that
        # exists; it deliberately doesn't add its own error message so the
        # two checks don't both fire for the same statement.
        if not self._function_return_stack:
            return self.visitChildren(ctx)

        expected = self._function_return_stack[-1]
        actual: Type = VoidType() if ctx.expression() is None else self._visit_type(ctx.expression())

        if not isinstance(actual, ErrorType) and not actual.is_assignable_to(expected):
            self._error(ctx, f"el valor de retorno debe ser de tipo {expected}; se encontró {actual}")
        return None

    # ── Persona 3: Control de Flujo + Clases + Arreglos + Generales ─────

    def visitIfStatement(self, ctx: CompiscriptParser.IfStatementContext):
        # TODO(Persona 3): condition expression must be boolean.
        return self.visitChildren(ctx)

    def visitWhileStatement(self, ctx: CompiscriptParser.WhileStatementContext):
        # TODO(Persona 3): condition must be boolean; track "inside a
        # loop" (e.g. a counter on self, incremented/decremented around
        # visitChildren) so break/continue can check it.
        return self.visitChildren(ctx)

    def visitDoWhileStatement(self, ctx: CompiscriptParser.DoWhileStatementContext):
        # TODO(Persona 3): same as visitWhileStatement.
        return self.visitChildren(ctx)

    def visitForStatement(self, ctx: CompiscriptParser.ForStatementContext):
        # TODO(Persona 3): condition boolean; same loop-tracking as while.
        return self.visitChildren(ctx)

    def visitSwitchStatement(self, ctx: CompiscriptParser.SwitchStatementContext):
        # TODO(Persona 3): switch expression type should be
        # compatible/comparable with each case's expression type.
        return self.visitChildren(ctx)

    def visitBreakStatement(self, ctx: CompiscriptParser.BreakStatementContext):
        # TODO(Persona 3): error if not inside a loop.
        return self.visitChildren(ctx)

    def visitContinueStatement(self, ctx: CompiscriptParser.ContinueStatementContext):
        # TODO(Persona 3): error if not inside a loop.
        return self.visitChildren(ctx)

    def visitPropertyAccessExpr(self, ctx: CompiscriptParser.PropertyAccessExprContext):
        # TODO(Persona 3): resolve the attribute/method on the target's
        # ClassType (walk .parent for inherited members).
        return self.visitChildren(ctx)

    def visitNewExpr(self, ctx: CompiscriptParser.NewExprContext):
        # TODO(Persona 3): class must exist; constructor arity/types must
        # match (if the class declares a `constructor` method).
        return self.visitChildren(ctx)

    def visitThisExpr(self, ctx: CompiscriptParser.ThisExprContext):
        # TODO(Persona 3): error if used outside a CLASS scope
        # (self.symbols.current.enclosing(ScopeKind.CLASS) is None).
        return self.visitChildren(ctx)

    def visitIndexExpr(self, ctx: CompiscriptParser.IndexExprContext):
        # TODO(Persona 3): target must be ArrayType; index expression must
        # be integer. (Bounds are a runtime concern, not static -- only
        # type-check here.)
        return self.visitChildren(ctx)

    def visitArrayLiteral(self, ctx: CompiscriptParser.ArrayLiteralContext):
        # TODO(Persona 3): all elements must share a compatible type;
        # result is ArrayType(that type). Empty `[]` -> coordinate with
        # Persona 2 on how UnknownType/inference should handle this.
        return self.visitChildren(ctx)
