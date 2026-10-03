"""Generador TAC que combina los mixins y las anotaciones semánticas."""
from __future__ import annotations

from CompiscriptVisitor import CompiscriptVisitor
from semantic.checker import SemanticChecker
from semantic.symbols import Scope, ScopeKind, Symbol, SymbolKind
from semantic.types import Type
from tac.emitter import Emitter
from tac.gen_classes import ClassMixin
from tac.gen_control import ControlMixin
from tac.gen_core import CoreMixin
from tac.gen_functions import FunctionMixin


class TACGenerator(
    CoreMixin,
    ControlMixin,
    FunctionMixin,
    ClassMixin,
    CompiscriptVisitor,
):
    def __init__(self, checker: SemanticChecker) -> None:
        self.checker = checker
        self.e = Emitter()
        self.break_labels: list[str] = []
        self.continue_labels: list[str] = []
        self._symbol_scopes: dict[int, Scope] = {}
        self._names: dict[int, str] = {}
        self._used_names: dict[int, set[str]] = {}
        self._reserved_names: dict[int, set[str]] = {}
        self._index_scopes(checker.symbols.global_scope)

    def expr(self, ctx) -> str | None:
        """Devuelve el operando de una expresión; void puede dar None."""
        return self.visit(ctx)

    def type_of(self, ctx) -> Type | None:
        """Consulta el tipo registrado durante el análisis semántico."""
        return self.checker.node_types.get(id(ctx))

    def symbol_of(self, ctx) -> Symbol | None:
        """Consulta el símbolo declarado o resuelto para el nodo."""
        return self.checker.node_symbols.get(id(ctx))

    def scope_of(self, ctx) -> Scope:
        """Devuelve el ámbito vigente al entrar al nodo."""
        return self.checker.node_scopes[id(ctx)]

    @staticmethod
    def _unit_scope(scope: Scope) -> Scope:
        """Encuentra la función, clase o ámbito global contenedor."""
        while (
            scope.parent is not None
            and scope.kind not in (ScopeKind.FUNCTION, ScopeKind.CLASS)
        ):
            scope = scope.parent
        return scope

    def _index_scopes(self, scope: Scope) -> None:
        """Relaciona cada símbolo con su ámbito de declaración."""
        unit_key = id(self._unit_scope(scope))
        reserved = self._reserved_names.setdefault(unit_key, set())
        used = self._used_names.setdefault(unit_key, set())

        for symbol in scope.symbols.values():
            self._symbol_scopes[id(symbol)] = scope
            reserved.add(symbol.name)

            # Los parámetros conservan su nombre aunque un bloque
            # interno declare otra variable con el mismo nombre.
            if symbol.kind is SymbolKind.PARAMETER:
                self._names[id(symbol)] = symbol.name
                used.add(symbol.name)

        for child in scope.children:
            self._index_scopes(child)

    def name_of(self, symbol: Symbol) -> str:
        """Devuelve un nombre estable para la identidad del símbolo."""
        symbol_key = id(symbol)
        if symbol_key in self._names:
            return self._names[symbol_key]

        scope = self._symbol_scopes[symbol_key]
        name = symbol.name

        if symbol.kind is SymbolKind.FUNCTION:
            if scope.kind is ScopeKind.CLASS:
                name = f"{scope.owner}.{name}"
        elif symbol.kind is SymbolKind.CLASS or scope.kind is ScopeKind.CLASS:
            pass
        else:
            unit_key = id(self._unit_scope(scope))
            used = self._used_names[unit_key]
            reserved = self._reserved_names[unit_key]
            suffix = 0

            while name in used or (suffix > 0 and name in reserved):
                suffix += 1
                name = f"{symbol.name}_{suffix}"

            used.add(name)

        self._names[symbol_key] = name
        return name

    def _check_implemented(self, tree) -> None:
        """Detecta reglas pendientes antes de emitir TAC incompleto."""
        pending_rules = {
            "FunctionDeclaration",
            "ReturnStatement",
            "CallExpr",
            "ClassDeclaration",
            "NewExpr",
            "ThisExpr",
            "PropertyAccessExpr",
            "PropertyAssignExpr",
        }

        nodes = [tree]
        while nodes:
            node = nodes.pop()
            rule = type(node).__name__.removesuffix("Context")
            requires_implementation = rule in pending_rules

            if rule == "LeftHandSide" and node.suffixOp():
                requires_implementation = True

            if requires_implementation:
                method_name = f"visit{rule}"
                actual = getattr(type(self), method_name, None)
                default = getattr(CompiscriptVisitor, method_name, None)
                if actual is default:
                    raise NotImplementedError(
                        f"TAC pendiente de implementación: {method_name}"
                    )

            for index in range(node.getChildCount() - 1, -1, -1):
                nodes.append(node.getChild(index))

    def visitProgram(self, ctx) -> list[str]:
        """Agrupa las sentencias de nivel superior en __main."""
        self._check_implemented(ctx)
        self.e.begin_unit("func __main():")
        for statement in ctx.statement():
            self.visit(statement)
        self.e.end_unit("endfunc")
        return self.e.lines()

    def visitBlock(self, ctx) -> None:
        """Visita las sentencias; el checker ya resolvió sus ámbitos."""
        for statement in ctx.statement():
            self.visit(statement)

    def visitStatement(self, ctx):
        """Delega en la construcción contenida en la sentencia."""
        return self.visit(ctx.getChild(0))
