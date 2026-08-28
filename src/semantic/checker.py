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

from CompiscriptParser import CompiscriptParser
from CompiscriptVisitor import CompiscriptVisitor

from semantic.errors import SemanticErrorList
from semantic.symbols import SymbolTable

Ctx = object  # any ANTLR ParserRuleContext -- avoids importing every *Context class here


class SemanticChecker(CompiscriptVisitor):
    def __init__(self) -> None:
        self.symbols = SymbolTable()
        self.errors = SemanticErrorList()

    def check(self, tree: Ctx) -> SemanticErrorList:
        self.visit(tree)
        return self.errors

    # ── helpers ──────────────────────────────────────────────────────────

    def _error(self, ctx: Ctx, message: str) -> None:
        """Record a semantic error anchored at the start token of `ctx`."""
        self.errors.add(ctx.start.line, ctx.start.column, message)

    # ── Persona 1: Tabla de Símbolos + Ámbito ───────────────────────────
    # declare/resolve via self.symbols (SymbolTable, see symbols.py);
    # push/pop scopes with self.symbols.enter_scope(...)/.exit_scope().

    def visitBlock(self, ctx: CompiscriptParser.BlockContext):
        # TODO(Persona 1): enter_scope(ScopeKind.BLOCK) around visitChildren,
        # exit_scope() in a finally. Also where "código muerto" (statements
        # after return/break/continue) is naturally detected -- Persona 3.
        return self.visitChildren(ctx)

    def visitVariableDeclaration(self, ctx: CompiscriptParser.VariableDeclarationContext):
        # TODO(Persona 1): declare in current scope, error on redeclaration
        # in the *same* scope (resolve_local, not resolve). Type comes from
        # typeAnnotation/initializer -- coordinate with Persona 2.
        return self.visitChildren(ctx)

    def visitClassDeclaration(self, ctx: CompiscriptParser.ClassDeclarationContext):
        # TODO(Persona 1): enter_scope(ScopeKind.CLASS), register members
        # (Persona 3 needs this for '.' access and `this`).
        return self.visitChildren(ctx)

    def visitIdentifierExpr(self, ctx: CompiscriptParser.IdentifierExprContext):
        # TODO(Persona 1): resolve(name); error "variable no declarada" if
        # None. Return the symbol's Type on success.
        return self.visitChildren(ctx)

    def visitAssignment(self, ctx: CompiscriptParser.AssignmentContext):
        # TODO(Persona 1): this is the statement-level rule
        # (`Identifier '=' expression ';'` or the property-assignment
        # alternative), NOT visitAssignExpr below -- `statement` tries
        # `assignment` before `expressionStatement`, so a plain `x = 5;`
        # always parses through *this* method. visitAssignExpr (Persona 2)
        # only fires when an assignment shows up nested inside a larger
        # expression (e.g. `print(x = 5)`), which is rare in practice.
        # For the plain-identifier alternative: resolve(name), error
        # "variable no declarada" if None -- same rule as
        # visitIdentifierExpr, just on the lhs. Coordinate with Persona 2
        # on the rhs-type-must-be-assignable check (shared with
        # visitAssignExpr's TODO) so the logic isn't duplicated. The
        # property-assignment alternative overlaps with Persona 3's
        # '.' access work (visitPropertyAccessExpr) -- whoever gets here
        # first should tag the other.
        return self.visitChildren(ctx)

    def visitForeachStatement(self, ctx: CompiscriptParser.ForeachStatementContext):
        # TODO(Persona 1): the iterated expression must be an ArrayType;
        # error otherwise. enter_scope(ScopeKind.BLOCK) for the body and
        # declare the loop variable there with the array's element type
        # (see types.py ArrayType.element), exit_scope() in a finally --
        # same shape as visitBlock above. Persona 3 also needs this scope
        # to exist so foreach bodies support break/continue like other
        # loops (their loop-tracking counter should increment here too).
        return self.visitChildren(ctx)

    def visitTryCatchStatement(self, ctx: CompiscriptParser.TryCatchStatementContext):
        # TODO(Persona 1, tentative -- confirm scope/typing decision with
        # the team, this wasn't in the original division): `try` block
        # needs its own BLOCK scope. `catch (err)` binds `err` in a new
        # BLOCK scope over the catch block only; its type isn't specified
        # anywhere in docs/plan-proyecto1.md -- suggest StringType or a
        # dedicated ErrorType-like type for the caught value, decide as a
        # team before implementing so it's not redone.
        return self.visitChildren(ctx)

    # ── Persona 2: Sistema de Tipos + Funciones ─────────────────────────

    def visitConstantDeclaration(self, ctx: CompiscriptParser.ConstantDeclarationContext):
        # TODO(Persona 2): initializer is mandatory for const (grammar
        # already enforces this syntactically -- '=' expression is
        # required, not optional -- so this is really about checking the
        # expression's type matches typeAnnotation, if present).
        return self.visitChildren(ctx)

    def visitAdditiveExpr(self, ctx: CompiscriptParser.AdditiveExprContext):
        # TODO(Persona 2): operands must be integer/float (promote to
        # float on a mix); '+' also needs to decide whether string
        # concatenation is allowed here -- confirm with the team.
        return self.visitChildren(ctx)

    def visitMultiplicativeExpr(self, ctx: CompiscriptParser.MultiplicativeExprContext):
        # TODO(Persona 2): same numeric rules as visitAdditiveExpr.
        return self.visitChildren(ctx)

    def visitUnaryExpr(self, ctx: CompiscriptParser.UnaryExprContext):
        # TODO(Persona 2): '-' requires an integer/float operand (result
        # keeps that type); '!' requires a boolean operand (result is
        # boolean). No TODO existed for this rule before -- same family as
        # visitAdditiveExpr/visitMultiplicativeExpr above.
        return self.visitChildren(ctx)
 
    def visitTernaryExpr(self, ctx: CompiscriptParser.TernaryExprContext):
        # TODO(Persona 2): only has a real ternary when the '?' alt is
        # present (grammar makes it optional -- check ctx for the '?'
        # token or the child count before treating this as anything but a
        # passthrough of logicalOrExpr). Condition must be boolean; the
        # two branch expressions must share/unify to a common type (or one
        # promotes to the other per is_assignable_to) -- that result type
        # is the ternary's type. No TODO existed for this rule before.
        return self.visitChildren(ctx)

    def visitLogicalOrExpr(self, ctx: CompiscriptParser.LogicalOrExprContext):
        # TODO(Persona 2): operands must be boolean.
        return self.visitChildren(ctx)

    def visitLogicalAndExpr(self, ctx: CompiscriptParser.LogicalAndExprContext):
        # TODO(Persona 2): operands must be boolean.
        return self.visitChildren(ctx)

    def visitEqualityExpr(self, ctx: CompiscriptParser.EqualityExprContext):
        # TODO(Persona 2): operands must be the same/compatible type.
        return self.visitChildren(ctx)

    def visitRelationalExpr(self, ctx: CompiscriptParser.RelationalExprContext):
        # TODO(Persona 2): operands must be numeric (integer/float).
        return self.visitChildren(ctx)

    def visitAssignExpr(self, ctx: CompiscriptParser.AssignExprContext):
        # TODO(Persona 2): rhs type must be assignable to lhs's declared
        # type (Type.is_assignable_to). Also where UnknownType (see
        # types.py) gets narrowed on first assignment.
        return self.visitChildren(ctx)

    def visitFunctionDeclaration(self, ctx: CompiscriptParser.FunctionDeclarationContext):
        # TODO(Persona 2): build a FunctionType from parameters/return
        # type, declare it (Persona 1's SymbolTable.declare) so recursive
        # calls resolve; enter_scope(ScopeKind.FUNCTION) for the body
        # (Persona 1). Closures: a nested visitFunctionDeclaration should
        # just work via the normal Scope.parent chain -- verify with a test.
        return self.visitChildren(ctx)

    def visitCallExpr(self, ctx: CompiscriptParser.CallExprContext):
        # TODO(Persona 2): arity + positional type-check against the
        # callee's FunctionType.
        return self.visitChildren(ctx)

    def visitReturnStatement(self, ctx: CompiscriptParser.ReturnStatementContext):
        # TODO(Persona 2): expression type must match the enclosing
        # function's declared return type. "must be inside a function at
        # all" is Persona 3's rule (control de flujo) -- both checks live
        # here since they read the same enclosing-function scope.
        return self.visitChildren(ctx)

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
