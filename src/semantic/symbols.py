"""Symbol table: `Scope` (name -> Symbol + parent pointer) and
`SymbolTable` (the stack of open scopes during a walk).

Independent of the ANTLR classes on purpose, so the TAC/MIPS phases can
reuse it as-is.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from semantic.types import Type


class SymbolKind(Enum):
    VARIABLE = auto()
    CONSTANT = auto()
    PARAMETER = auto()
    FUNCTION = auto()
    CLASS = auto()


@dataclass
class Symbol:
    name: str
    kind: SymbolKind
    type: Type
    line: int
    column: int
    # Reserved for TAC/MIPS (offset, register). Unused here.
    address: Optional[int] = None


class ScopeKind(Enum):
    GLOBAL = auto()
    FUNCTION = auto()
    CLASS = auto()
    BLOCK = auto()


@dataclass
class Scope:
    """One node of the scope tree.

    `parent` is what `resolve` walks; `children` is what makes this a
    permanent tree and not just the stack of open scopes -- a scope is
    popped off the stack on the way out, but stays hanging off its
    parent. That tree feeds the IDE panel and projects 2/3.
    """

    kind: ScopeKind
    parent: Optional["Scope"] = None
    symbols: dict[str, Symbol] = field(default_factory=dict)
    children: list["Scope"] = field(default_factory=list)
    # Function/class owning this scope, None for GLOBAL and bare blocks.
    # Unused here; for projects 2/3.
    owner: Optional[str] = None

    def to_dict(self) -> dict:
        """JSON view of this subtree, for the IDE panel."""
        return {
            "kind": self.kind.name,
            "owner": self.owner,
            "symbols": [
                {
                    "name": symbol.name,
                    "kind": symbol.kind.name,
                    "type": str(symbol.type),
                    "line": symbol.line,
                    "column": symbol.column,
                }
                for symbol in self.symbols.values()
            ],
            "children": [child.to_dict() for child in self.children],
        }

    def declare(self, symbol: Symbol) -> bool:
        """Declare in *this* scope. False if the name was already taken:
        the checker reports it, since it has the line and the message."""
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True

    def resolve_local(self, name: str) -> Optional[Symbol]:
        """This scope only. For redeclaration checks and class members,
        which must not fall through to the enclosing scope."""
        return self.symbols.get(name)

    def resolve(self, name: str) -> Optional[Symbol]:
        """Lexical lookup: this scope, then its parent, up to global."""
        scope: Optional[Scope] = self
        while scope is not None:
            found = scope.symbols.get(name)
            if found is not None:
                return found
            scope = scope.parent
        return None

    def enclosing(self, kind: ScopeKind) -> Optional["Scope"]:
        """Nearest ancestor (or self) of that kind -- e.g. CLASS to
        resolve `this`."""
        scope: Optional[Scope] = self
        while scope is not None:
            if scope.kind == kind:
                return scope
            scope = scope.parent
        return None


class SymbolTable:
    """Stack of open scopes during the walk."""

    def __init__(self) -> None:
        self.global_scope = Scope(ScopeKind.GLOBAL)
        self._stack: list[Scope] = [self.global_scope]

    @property
    def current(self) -> Scope:
        return self._stack[-1]

    def enter_scope(self, kind: ScopeKind, owner: Optional[str] = None) -> Scope:
        scope = Scope(kind, parent=self.current, owner=owner)
        # Into the permanent tree, not just the stack.
        self.current.children.append(scope)
        self._stack.append(scope)
        return scope

    def exit_scope(self) -> Scope:
        """Always in a try/finally next to enter_scope, so an error
        midway through doesn't leave the stack unbalanced."""
        return self._stack.pop()

    def declare(self, symbol: Symbol) -> bool:
        return self.current.declare(symbol)

    def resolve(self, name: str) -> Optional[Symbol]:
        return self.current.resolve(name)
