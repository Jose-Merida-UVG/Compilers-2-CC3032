"""Symbol table.

A `Scope` is a flat name -> Symbol table with a pointer to its parent scope
(global -> class/function -> nested block, following normal lexical
scoping). `SymbolTable` is the stack of currently-open scopes during a tree
walk, plus the operations the checker needs day to day: declare, resolve,
enter/exit scope.

Kept independent of the ANTLR-generated parser classes on purpose, so it's
reusable as-is by the TAC/MIPS phases later (see docs/plan-proyecto1.md) --
that's also why `Symbol.address` exists already but stays unused (None)
until that phase needs it.
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
    # Reserved for later compiler phases (TAC/MIPS): memory offset,
    # register, activation-record slot, etc. Left as None here on purpose.
    address: Optional[int] = None


class ScopeKind(Enum):
    GLOBAL = auto()
    FUNCTION = auto()
    CLASS = auto()
    BLOCK = auto()


@dataclass
class Scope:
    kind: ScopeKind
    parent: Optional["Scope"] = None
    symbols: dict[str, Symbol] = field(default_factory=dict)

    def declare(self, symbol: Symbol) -> bool:
        """Add a symbol to *this* scope. Returns False if the name is
        already declared in this same scope (redeclaration) -- turning
        that into a SemanticError is the caller's (checker's) job, since
        only the checker has the line/column of the *new* declaration and
        the wording of the message."""
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True

    def resolve_local(self, name: str) -> Optional[Symbol]:
        """Look up `name` in this scope only, ignoring parents. Used for
        redeclaration checks and for class-member lookup (which should
        NOT fall through to an enclosing lexical scope)."""
        return self.symbols.get(name)

    def resolve(self, name: str) -> Optional[Symbol]:
        """Normal lexical lookup: this scope, then its parent, and so on
        up to the global scope."""
        scope: Optional[Scope] = self
        while scope is not None:
            found = scope.symbols.get(name)
            if found is not None:
                return found
            scope = scope.parent
        return None

    def enclosing(self, kind: ScopeKind) -> Optional["Scope"]:
        """Nearest ancestor scope (or self) of the given kind -- e.g.
        `enclosing(ScopeKind.FUNCTION)` to validate `return`, or
        `enclosing(ScopeKind.CLASS)` to resolve `this`."""
        scope: Optional[Scope] = self
        while scope is not None:
            if scope.kind == kind:
                return scope
            scope = scope.parent
        return None


class SymbolTable:
    """The stack of open scopes during a single tree walk. One instance per
    `SemanticChecker` run (see checker.py)."""

    def __init__(self) -> None:
        self.global_scope = Scope(ScopeKind.GLOBAL)
        self._stack: list[Scope] = [self.global_scope]

    @property
    def current(self) -> Scope:
        return self._stack[-1]

    def enter_scope(self, kind: ScopeKind) -> Scope:
        scope = Scope(kind, parent=self.current)
        self._stack.append(scope)
        return scope

    def exit_scope(self) -> Scope:
        """Pop and return the current scope. Callers should always pair
        this with `enter_scope` (a try/finally in the checker), so a
        semantic error midway through a block doesn't leave the stack
        unbalanced for the rest of the walk."""
        return self._stack.pop()

    def declare(self, symbol: Symbol) -> bool:
        return self.current.declare(symbol)

    def resolve(self, name: str) -> Optional[Symbol]:
        return self.current.resolve(name)
