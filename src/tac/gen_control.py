"""ControlMixin: TAC para sentencias de control de flujo.

Reglas de la gramática que implementa (docs/proyecto2/00-contrato.md
§4.1): ifStatement, whileStatement, doWhileStatement, forStatement,
breakStatement y continueStatement. (foreach, switch y try/catch se
agregan en la siguiente parte.)

Toda condición pasa por `self.gen_cond(cond, ltrue, lfalse, fall)` (ver
gen_core.py): se pasa en `fall` la etiqueta que se colocará justo después,
para que no sobren `goto`. Las etiquetas que solo pueden estar sin
referenciar (cuerpo, `else`, fin del bucle) se colocan con
`self._label_if_used`; las de inicio de bucle siempre se colocan porque
el salto de regreso las referencia.

`break`/`continue` leen los extremos de las pilas `self.break_labels` y
`self.continue_labels` (listas creadas por el esqueleto de Cami); cada
bucle apila sus etiquetas mientras genera el cuerpo.

Esquemas (L? = etiqueta nueva):

    if (c) A else B        while (c) A            do A while (c)
        <gen_cond c>       Lcond:                 Lbody:
        A                      <gen_cond c>           A
        goto Lend          Lbody:                 Lcond:
    Lelse:                     A                      <gen_cond c>
        B                      goto Lcond         Lend:
    Lend:                  Lend:
"""

from __future__ import annotations

from CompiscriptParser import CompiscriptParser


class ControlMixin:
    # ── Utilidades ──────────────────────────────────────────────────────
    @staticmethod
    def _ends_with_jump(block) -> bool:
        """¿El bloque termina en return/break/continue? Entonces el salto
        que lo seguiría es código muerto y se omite."""
        statements = block.statement()
        if not statements:
            return False
        last = statements[-1]
        return bool(last.returnStatement() or last.breakStatement() or last.continueStatement())

    def _loop_body(self, block, break_label: str, continue_label: str) -> None:
        self.break_labels.append(break_label)
        self.continue_labels.append(continue_label)
        try:
            self.visit(block)
        finally:
            self.break_labels.pop()
            self.continue_labels.pop()

    # ── if / else ───────────────────────────────────────────────────────
    def visitIfStatement(self, ctx: CompiscriptParser.IfStatementContext):
        then_block = ctx.block(0)
        else_block = ctx.block(1) if len(ctx.block()) > 1 else None
        ltrue, lfalse = self.e.new_label(), self.e.new_label()

        self.gen_cond(ctx.expression(), ltrue, lfalse, fall=ltrue)
        self._label_if_used(ltrue)
        self.visit(then_block)

        if else_block is None:
            self._label_if_used(lfalse)
            return None

        lend = self.e.new_label()
        if not self._ends_with_jump(then_block):
            self._jump_to("", lend)
        self._label_if_used(lfalse)
        self.visit(else_block)
        self._label_if_used(lend)
        return None

    # ── bucles ──────────────────────────────────────────────────────────
    def visitWhileStatement(self, ctx: CompiscriptParser.WhileStatementContext):
        lcond, lbody, lend = (self.e.new_label() for _ in range(3))
        self.e.emit_label(lcond)  # siempre referenciada por el salto de regreso
        self.gen_cond(ctx.expression(), lbody, lend, fall=lbody)
        self._label_if_used(lbody)
        self._loop_body(ctx.block(), break_label=lend, continue_label=lcond)
        self._jump_to("", lcond)
        self._label_if_used(lend)
        return None

    def visitDoWhileStatement(self, ctx: CompiscriptParser.DoWhileStatementContext):
        lbody, lcond, lend = (self.e.new_label() for _ in range(3))
        self.e.emit_label(lbody)
        self._loop_body(ctx.block(), break_label=lend, continue_label=lcond)
        self._label_if_used(lcond)  # solo si hubo `continue`
        self.gen_cond(ctx.expression(), lbody, lend, fall=lend)
        self._label_if_used(lend)
        return None

    def visitForStatement(self, ctx: CompiscriptParser.ForStatementContext):
        # 'for' '(' (variableDeclaration | assignment | ';') cond? ';' update? ')' block
        # Las dos expresiones son opcionales, así que se distinguen por
        # su posición respecto al `;` que separa condición y actualización
        # (variableDeclaration y assignment ya traen el suyo adentro).
        if ctx.variableDeclaration() is not None:
            self.visit(ctx.variableDeclaration())
        elif ctx.assignment() is not None:
            self.visit(ctx.assignment())
        # Hijos: 0 'for', 1 '(', 2 init (o su `;`), luego `[cond] ; [update] )`.
        cond = update = None
        seen_semicolon = False
        for i in range(3, ctx.getChildCount()):
            child = ctx.getChild(i)
            if isinstance(child, CompiscriptParser.ExpressionContext):
                if seen_semicolon:
                    update = child
                else:
                    cond = child
            elif child.getText() == ";":
                seen_semicolon = True

        lstart, lbody, lupdate, lend = (self.e.new_label() for _ in range(4))
        self.e.emit_label(lstart)
        if cond is not None:
            self.gen_cond(cond, lbody, lend, fall=lbody)
            self._label_if_used(lbody)
        self._loop_body(ctx.block(), break_label=lend, continue_label=lupdate)
        self._label_if_used(lupdate)  # solo si hubo `continue`
        if update is not None:
            result = self.expr(update)
            if result:
                self.e.free(result)
        self._jump_to("", lstart)
        self._label_if_used(lend)
        return None

    # ── break / continue ────────────────────────────────────────────────
    def visitBreakStatement(self, ctx: CompiscriptParser.BreakStatementContext):
        self._jump_to("", self.break_labels[-1])
        return None

    def visitContinueStatement(self, ctx: CompiscriptParser.ContinueStatementContext):
        self._jump_to("", self.continue_labels[-1])
        return None
