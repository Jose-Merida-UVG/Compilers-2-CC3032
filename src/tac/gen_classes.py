"""ClassMixin: TAC de clases, objetos, herencia y la cadena `leftHandSide`.

Cada clase es una unidad `class … endclass` con un `__init_fields(this)`
sintetizado (llama al del padre y asigna los campos con valor inicial) y sus
métodos. `new` reserva el objeto, evalúa los argumentos y llama a
`__init_fields` y luego al constructor. Los métodos se resuelven de forma
estática: se llama a la etiqueta del ancestro más cercano que lo declara, sin
despacho dinámico.

`eval_chain` recorre `primaryAtom suffixOp*` con un operando base que cada
sufijo transforma (`[i]` carga, `.campo` carga, `.m(...)` llama con el objeto
como receptor).
"""

from __future__ import annotations

from typing import Optional

from CompiscriptParser import CompiscriptParser

from semantic.symbols import ScopeKind, Symbol, SymbolKind
from semantic.types import ClassType
from tac.instructions import (
    END_CLASS,
    END_FUNCTION,
    call_instruction,
    class_header,
    function_header,
)

THIS = "this"
INIT_FIELDS = "__init_fields"


class ClassMixin:
    def visitClassDeclaration(self, ctx: CompiscriptParser.ClassDeclarationContext):
        identifiers = ctx.Identifier()
        name = identifiers[0].getText()
        parent = identifiers[1].getText() if len(identifiers) > 1 else None

        self.e.begin_unit(class_header(name, parent))
        self._emit_init_fields(ctx, name, parent)
        for member in ctx.classMember():
            if member.functionDeclaration() is not None:
                self.visit(member.functionDeclaration())
        self.e.end_unit(END_CLASS)
        return None

    def _emit_init_fields(self, ctx, name: str, parent: Optional[str]) -> None:
        """Emite `Clase.__init_fields`: campos del padre y luego los propios."""
        self.e.begin_unit(function_header(f"{name}.{INIT_FIELDS}", [THIS]))
        if parent is not None:
            self.e.emit(f"param {THIS}")
            self.e.emit(call_instruction(f"{parent}.{INIT_FIELDS}", 1))

        for member in ctx.classMember():
            declaration = member.variableDeclaration() or member.constantDeclaration()
            if declaration is None:
                continue
            if member.variableDeclaration() is not None:
                initializer = declaration.initializer()
                init = initializer.expression() if initializer is not None else None
            else:
                init = declaration.expression()
            if init is None:
                continue  # sin valor inicial no se emite nada
            field = self.symbol_of(declaration)
            value = self.expr(init)
            value = self._coerce(
                value, self.type_of(init), field.type if field is not None else None
            )
            field_name = declaration.Identifier().getText()
            self.e.emit(f"{THIS}.{field_name} = {value}")
            self.e.free(value)

        self.e.emit("return")
        self.e.end_unit(END_FUNCTION)

    def visitNewExpr(self, ctx: CompiscriptParser.NewExprContext):
        class_type = self.symbol_of(ctx).type
        assert isinstance(class_type, ClassType)

        # El objeto vive en este temporal hasta terminar las llamadas
        obj = self.e.new_temp()
        self.e.emit(f"{obj} = new {class_type.class_name}")

        constructor = self._find_member(class_type, "constructor")
        param_types = constructor[1].type.params if constructor is not None else []
        args = self._eval_args(ctx.arguments(), param_types)

        self.e.emit(f"param {obj}")
        self.e.emit(call_instruction(f"{class_type.class_name}.{INIT_FIELDS}", 1))
        if constructor is not None:
            self.e.emit(f"param {obj}")
            self._push_params(args)
            owner = constructor[0].class_name
            self.e.emit(call_instruction(f"{owner}.constructor", len(args) + 1))
        else:
            self._push_params(args)
        return obj

    def visitThisExpr(self, ctx: CompiscriptParser.ThisExprContext):
        return THIS

    @staticmethod
    def _find_member(class_type: ClassType, name: str) -> Optional[tuple[ClassType, Symbol]]:
        """Primer ancestro (incluida la propia clase) que declara `name`."""
        node: Optional[ClassType] = class_type
        while node is not None:
            member = node.members.get(name)
            if member is not None:
                return node, member
            node = node.parent
        return None

    def visitPropertyAssignExpr(self, ctx: CompiscriptParser.PropertyAssignExprContext):
        """`obj.campo = v` como expresión; devuelve el valor asignado."""
        lhs = ctx.lhs
        base = self.eval_chain(lhs, len(lhs.suffixOp()))
        value = self.expr(ctx.assignmentExpr())
        member = self.symbol_of(ctx)
        value = self._coerce(
            value, self.type_of(ctx.assignmentExpr()), member.type if member is not None else None
        )
        self.e.emit(f"{base}.{ctx.Identifier().getText()} = {value}")
        self.e.free(base)
        return value

    def visitLeftHandSide(self, ctx: CompiscriptParser.LeftHandSideContext):
        return self.eval_chain(ctx, len(ctx.suffixOp()))

    def _in_class_scope(self, symbol: Symbol) -> bool:
        scope = self._symbol_scopes.get(id(symbol))
        return scope is not None and scope.kind is ScopeKind.CLASS

    def _chain_start(self, atom) -> tuple[str, Optional[str]]:
        """Operando del átomo y, si es un método de la propia clase usado sin
        `this.`, el receptor implícito."""
        if isinstance(atom, CompiscriptParser.IdentifierExprContext):
            symbol = self.symbol_of(atom)
            if symbol is not None and self._in_class_scope(symbol):
                if symbol.kind in (SymbolKind.VARIABLE, SymbolKind.CONSTANT):
                    t = self.e.new_temp()
                    self.e.emit(f"{t} = {THIS}.{symbol.name}")
                    return t, None
                if symbol.kind is SymbolKind.FUNCTION:
                    return self.name_of(symbol), THIS
        return self.visit(atom), None

    def eval_chain(self, ctx, count: int) -> str:
        """Evalúa el átomo y los primeros `count` sufijos. Devuelve el operando
        resultante, o None si termina en una llamada sin valor. gen_core la usa
        con `count` sin el último sufijo para los destinos de asignación."""
        P = CompiscriptParser
        atom = ctx.primaryAtom()
        suffixes = list(ctx.suffixOp())[:count]
        whole = count == len(ctx.suffixOp())

        base, receiver = self._chain_start(atom)
        current_type = self.type_of(atom)

        for index, suffix in enumerate(suffixes):
            following = suffixes[index + 1] if index + 1 < len(suffixes) else None
            if isinstance(suffix, P.IndexExprContext):
                base = self.gen_index_load(base, self.visit(suffix))
            elif isinstance(suffix, P.PropertyAccessExprContext):
                member = self.symbol_of(suffix)
                if (
                    isinstance(following, P.CallExprContext)
                    and member is not None
                    and member.kind is SymbolKind.FUNCTION
                ):
                    # Llamada a método: el objeto pasa a ser el receptor
                    receiver, base = base, self.name_of(member)
                else:
                    self.e.free(base)
                    t = self.e.new_temp()
                    self.e.emit(f"{t} = {base}.{suffix.Identifier().getText()}")
                    base = t
            else:
                statement = whole and following is None and self._is_statement(ctx)
                base = self._emit_call(base, suffix, current_type, receiver, statement)
                receiver = None
            current_type = self.type_of(suffix)
        return base
