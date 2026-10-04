"""ControlMixin: TAC de if, ciclos, switch, break/continue y try/catch.

Toda condición pasa por `gen_cond(cond, ltrue, lfalse, fall)`; `fall` es la
etiqueta que se coloca justo después, para no emitir `goto` sobrantes. Cada
ciclo apila sus etiquetas en `break_labels` / `continue_labels` mientras genera
el cuerpo. El try/catch solo marca la región protegida (no hay `throw`):

        try Lcatch
        <bloque try>
        endtry
        goto Lend
    Lcatch:
        catch e
        <bloque catch>
    Lend:

`open_tries` cuenta los `try` abiertos: `break`, `continue` y `return` emiten un
`endtry` por cada uno del que salen.
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

    def _state(self) -> dict:
        """Profundidad de `try` en el momento de apilar cada etiqueta de
        break/continue (listas paralelas a break_labels/continue_labels).
        Creado perezosamente: un mixin no tiene __init__."""
        if not hasattr(self, "_ctl_state"):
            self._ctl_state = {"break": [], "continue": []}
        return self._ctl_state

    def _push_break(self, label: str) -> None:
        self.break_labels.append(label)
        self._state()["break"].append(getattr(self, "open_tries", 0))

    def _push_continue(self, label: str) -> None:
        self.continue_labels.append(label)
        self._state()["continue"].append(getattr(self, "open_tries", 0))

    def _pop_break(self) -> None:
        self.break_labels.pop()
        self._state()["break"].pop()

    def _pop_continue(self) -> None:
        self.continue_labels.pop()
        self._state()["continue"].pop()

    def _loop_body(self, block, break_label: str, continue_label: str) -> None:
        self._push_break(break_label)
        self._push_continue(continue_label)
        try:
            self.visit(block)
        finally:
            self._pop_break()
            self._pop_continue()

    def _leave_tries(self, depth_at_target: int) -> None:
        """`endtry` por cada try abierto desde que se apiló el destino."""
        for _ in range(getattr(self, "open_tries", 0) - depth_at_target):
            self.e.emit("endtry")

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

    # ── foreach ─────────────────────────────────────────────────────────
    def visitForeachStatement(self, ctx: CompiscriptParser.ForeachStatementContext):
        """foreach (x in arr) body: índice recorriendo `len arr`. El
        arreglo, la longitud y el índice son temporales fijados: viven
        todo el ciclo y se liberan al final."""
        name = self._ident(ctx, ctx.Identifier().getText())
        array = self.expr(ctx.expression())
        length = self.e.new_temp()
        self.e.emit(f"{length} = len {array}")
        index = self.e.new_temp()
        self.e.emit(f"{index} = 0")

        lcond, lupdate, lend = (self.e.new_label() for _ in range(3))
        self.e.emit_label(lcond)
        self._jump_to(f"if {index} >= {length} goto", lend)
        self.e.emit(f"{name} = {array}[{index}]")
        self._loop_body(ctx.block(), break_label=lend, continue_label=lupdate)
        self._label_if_used(lupdate)  # solo si hubo `continue`
        self.e.emit(f"{index} = {index} + 1")
        self._jump_to("", lcond)
        self.e.emit_label(lend)
        for temp in (index, length, array):
            self.e.free(temp)
        return None

    # ── switch ──────────────────────────────────────────────────────────
    def visitSwitchStatement(self, ctx: CompiscriptParser.SwitchStatementContext):
        """El valor se evalúa una vez; una cadena de `if v == caso goto`
        despacha, y los cuerpos van en orden: cada caso cae en el
        siguiente (el ejemplo de docs/DefinicionCompiscript.md imprime
        "uno", "dos" y "otro" para x = 1).

        `switch` NO es destino de `break`: la especificación del
        proyecto limita `break`/`continue` a bucles (el checker lo
        rechaza fuera de uno), así que dentro de un switch que está en
        un bucle, `break`/`continue` se refieren a ese bucle."""
        cases = ctx.switchCase()
        default = ctx.defaultCase()
        case_labels = [self.e.new_label() for _ in cases]
        ldefault = self.e.new_label() if default is not None else None
        lend = self.e.new_label()

        value = self.expr(ctx.expression())
        value_type = self.type_of(ctx.expression())
        for case, label in zip(cases, case_labels):
            candidate = self.expr(case.expression())
            candidate = self._coerce(candidate, self.type_of(case.expression()), value_type)
            self._jump_to(f"if {value} == {candidate} goto", label)
            self.e.free(candidate)
        self.e.free(value)  # ya no hace falta durante los cuerpos
        self._jump_to("", ldefault if ldefault is not None else lend)

        for case, label in zip(cases, case_labels):
            self.e.emit_label(label)
            for stmt in case.statement():
                self.visit(stmt)
        if default is not None:
            self.e.emit_label(ldefault)
            for stmt in default.statement():
                self.visit(stmt)
        self._label_if_used(lend)
        return None

    # ── try / catch ─────────────────────────────────────────────────────
    def visitTryCatchStatement(self, ctx: CompiscriptParser.TryCatchStatementContext):
        try_block, catch_block = ctx.block(0), ctx.block(1)
        lcatch, lend = self.e.new_label(), self.e.new_label()

        self._jump_to("try", lcatch)
        self.open_tries = getattr(self, "open_tries", 0) + 1
        try:
            self.visit(try_block)
        finally:
            self.open_tries -= 1
        if not self._ends_with_jump(try_block):
            # Si el bloque termina en return/break/continue, esa
            # sentencia ya emitió su `endtry`: otro sería código muerto.
            self.e.emit("endtry")
            self._jump_to("", lend)

        self.e.emit_label(lcatch)
        self.e.emit(f"catch {self._ident(ctx, ctx.Identifier().getText())}")
        self.visit(catch_block)
        self._label_if_used(lend)
        return None

    # ── break / continue ────────────────────────────────────────────────
    def visitBreakStatement(self, ctx: CompiscriptParser.BreakStatementContext):
        self._leave_tries(self._state()["break"][-1])
        self._jump_to("", self.break_labels[-1])
        return None

    def visitContinueStatement(self, ctx: CompiscriptParser.ContinueStatementContext):
        self._leave_tries(self._state()["continue"][-1])
        self._jump_to("", self.continue_labels[-1])
        return None
