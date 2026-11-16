"""Datos para el IDE: marcos y árbol de activación.

    frames  etiqueta -> {label, total_size, slots}
    tree    llamadas desplegadas desde `__main`, con la línea TAC de cada una

Una llamada recursiva se marca `recursive` y no se despliega; las llamadas
virtuales usan el método del tipo estático. El árbol se corta en `MAX_NODES`.
"""

from __future__ import annotations

from asm.frames import FrameInfo
from asm.ir import Call, CallVirt, FuncUnit, Program

ROOT = "__main"
MAX_NODES = 400


def build_activation(program: Program, frames: dict[str, FrameInfo]) -> dict:
    """Arma el diccionario que muestra el IDE (formato en el docstring del módulo)."""
    units: dict[str, FuncUnit] = {u.label: u for u in program.functions()}
    budget = [MAX_NODES]

    def expand(label: str, path: tuple[str, ...]) -> list[dict]:
        """Nodos hijos de `label`."""
        unit = units.get(label)
        children: list[dict] = []
        for ins in unit.body if unit else []:
            if isinstance(ins, Call):
                callee, virtual = ins.callee, False
            elif isinstance(ins, CallVirt) and ins.static_target:
                callee, virtual = ins.static_target, True
            else:
                continue
            node: dict = {"label": callee, "line": ins.line, "children": []}
            if virtual:
                node["virtual"] = True
            if callee in path or callee == label:
                node["recursive"] = True
                node["truncated"] = True
            elif budget[0] <= 0:
                node["truncated"] = True
            else:
                budget[0] -= 1
                node["children"] = expand(callee, path + (callee,))
            children.append(node)
        return children

    return {
        "frames": {
            label: {
                "label": label,
                "total_size": int(fr.unit.frame.get("total_size", 0)) + fr.caps_size,
                "slots": fr.slots(),
            }
            for label, fr in frames.items()
        },
        "tree": {"label": ROOT, "children": expand(ROOT, (ROOT,))},
    }
