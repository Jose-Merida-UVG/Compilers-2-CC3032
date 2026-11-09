"""Convenciones y helpers de formato para el TAC del contrato §3."""
from __future__ import annotations

INDENT = "    "
TEMP_PREFIX = "$t"
LABEL_PREFIX = "L"
MAIN_NAME = "__main"

BINARY_OPERATORS = frozenset(
    {"+", "-", "*", "/", "%", "==", "!=", "<", "<=", ">", ">="}
)
UNARY_OPERATORS = frozenset({"-", "!"})

END_FUNCTION = "endfunc"
END_CLASS = "endclass"


def function_header(name: str, parameters: list[str]) -> str:
    """Cabecera sin sangría: func f(a, b):"""
    return f"func {name}({', '.join(parameters)}):"


def class_header(name: str, parent: str | None = None) -> str:
    """Cabecera sin sangría, con herencia opcional."""
    inheritance = f" : {parent}" if parent is not None else ""
    return f"class {name}{inheritance}:"


def label_definition(name: str) -> str:
    """Etiqueta sin sangría: L1:"""
    return f"{name}:"


def call_instruction(
    name: str,
    argument_count: int,
    target: str | None = None,
    virtual: bool = False,
) -> str:
    """Llamada con destino opcional; el conteo incluye this. `virtual` es la
    llamada indirecta por la tabla de métodos (`name` es un temporal)."""
    call = f"{'callvirt' if virtual else 'call'} {name}, {argument_count}"
    return f"{target} = {call}" if target is not None else call
