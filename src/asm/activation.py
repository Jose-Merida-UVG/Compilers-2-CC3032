"""Datos del IDE: registros de activación y árbol de activación (Tono).

    frames  etiqueta -> {label, total_size, slots}  (de `FrameInfo.slots()`)
    tree    el grafo de llamadas desplegado desde `__main`; cada nodo es una
            llamada (`Call` o `CallVirt`) y lleva la línea TAC que la origina

Una llamada a una función que ya está en la rama se marca `recursive` y no se
despliega (`truncated`). `CallVirt` usa el método del tipo estático y se marca
`virtual`. El árbol se corta en `MAX_NODES` para que un grafo muy ramificado no
crezca sin límite.
"""

from __future__ import annotations

from asm.frames import FrameInfo
from asm.ir import Call, CallVirt, FuncUnit, Program

ROOT = "__main"
MAX_NODES = 400


def build_activation(program: Program, frames: dict[str, FrameInfo]) -> dict:
    units: dict[str, FuncUnit] = {u.label: u for u in program.functions()}
    budget = [MAX_NODES]

    def expand(label: str, path: tuple[str, ...]) -> list[dict]:
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
                "total_size": int(fr.unit.frame.get("total_size", 0)),
                "slots": fr.slots(),
            }
            for label, fr in frames.items()
        },
        "tree": {"label": ROOT, "children": expand(ROOT, (ROOT,))},
    }
