"""The Type hierarchy used by the semantic checker.

Every `visit*` method in `checker.py` that evaluates an expression returns
one of these. Kept independent of the ANTLR-generated parser classes on
purpose, so it stays reusable in the TAC/MIPS phases later (see
docs/plan-proyecto1.md).

Assignability rules (who can flow into whom) live in `is_assignable_to`,
per the decisions table in docs/plan-proyecto1.md:
  - integer -> float promotion allowed, never the reverse.
  - null is assignable to any array/class type (and to null itself), never
    to a primitive.
  - ErrorType absorbs everything both ways, so one bad subexpression never
    cascades into a wall of unrelated errors above it.
  - UnknownType (a `let x;` with no annotation and no initializer) accepts
    anything; the checker is responsible for narrowing it to a concrete
    type the first time it sees an assignment, and for erroring if it's
    used before that happens.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class Type:
    """Base class for all types."""

    name: str = "type"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Type) and type(self) is type(other)

    def __hash__(self) -> int:
        return hash(type(self))

    def __repr__(self) -> str:
        return self.name

    def is_assignable_to(self, target: "Type") -> bool:
        """Can a value of this type be assigned/passed where `target` is
        expected? Default: exact type match. Subclasses override this for
        numeric promotion, null, class inheritance, etc."""
        if isinstance(self, ErrorType) or isinstance(target, ErrorType):
            return True
        return self == target


class ErrorType(Type):
    """Returned after a semantic error so a bad subexpression doesn't
    trigger a cascade of unrelated errors above it in the tree."""

    name = "error"


class VoidType(Type):
    """Return type of a function with no `: type` annotation and no
    `return <expr>` anywhere in its body."""

    name = "void"


class UnknownType(Type):
    """`let x;` -- no annotation, no initializer. Resolved to a concrete
    type on first assignment (see decisions table)."""

    name = "unknown"

    def is_assignable_to(self, target: "Type") -> bool:
        return True


class NullType(Type):
    name = "null"

    def is_assignable_to(self, target: "Type") -> bool:
        if isinstance(target, (ArrayType, ClassType, NullType)):
            return True
        return super().is_assignable_to(target)


class BooleanType(Type):
    name = "boolean"


class IntegerType(Type):
    name = "integer"

    def is_assignable_to(self, target: "Type") -> bool:
        if isinstance(target, (IntegerType, FloatType)):
            return True
        return super().is_assignable_to(target)


class FloatType(Type):
    name = "float"


class StringType(Type):
    name = "string"


@dataclass(eq=False, repr=False)
class ArrayType(Type):
    element: Type

    @property
    def name(self) -> str:  # type: ignore[override]
        return f"{self.element}[]"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ArrayType) and self.element == other.element

    def __hash__(self) -> int:
        return hash(("array", self.element))

    def is_assignable_to(self, target: "Type") -> bool:
        if isinstance(target, ArrayType):
            return self.element == target.element
        return super().is_assignable_to(target)


@dataclass(eq=False, repr=False)
class FunctionType(Type):
    params: list[Type]
    ret: Type

    @property
    def name(self) -> str:  # type: ignore[override]
        params = ", ".join(str(p) for p in self.params)
        return f"({params}) -> {self.ret}"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, FunctionType)
            and self.params == other.params
            and self.ret == other.ret
        )

    def __hash__(self) -> int:
        return hash(("function", tuple(self.params), self.ret))


@dataclass(eq=False, repr=False)
class ClassType(Type):
    class_name: str
    parent: Optional["ClassType"] = None

    @property
    def name(self) -> str:  # type: ignore[override]
        return self.class_name

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ClassType) and self.class_name == other.class_name

    def __hash__(self) -> int:
        return hash(("class", self.class_name))

    def is_subclass_of(self, other: "ClassType") -> bool:
        node: Optional[ClassType] = self
        while node is not None:
            if node.class_name == other.class_name:
                return True
            node = node.parent
        return False

    def is_assignable_to(self, target: "Type") -> bool:
        if isinstance(target, ClassType):
            return self.is_subclass_of(target)
        return super().is_assignable_to(target)


# Name -> primitive Type, for resolving a `baseType` parse node
# ('boolean' | 'integer' | 'float' | 'string') to its Type instance.
PRIMITIVE_TYPES: dict[str, Type] = {
    "boolean": BooleanType(),
    "integer": IntegerType(),
    "float": FloatType(),
    "string": StringType(),
}
