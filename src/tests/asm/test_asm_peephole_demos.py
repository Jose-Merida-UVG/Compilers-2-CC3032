"""Un demo por regla de la mirilla (`workspace/input/comp-mips/17-mirilla-<regla>-valido.cps`).

Cada demo debe (1) activar su regla en el compilador real, (2) imprimir lo
calculado a mano con y sin mirilla, y (3) quedar con menos líneas optimizado.
`move_redundante` y `guardar_tras_cargar` no tienen demo: el generador nunca emite
esos patrones, así que solo se prueban sobre líneas sueltas en test_asm_peephole.py.
"""

from __future__ import annotations

import os

import pytest
from antlr4 import FileStream

from asm.generator import generate_asm
from asm.peephole import optimize
from compiler import analyze
from support.minisim import Sim

DEMOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "workspace", "input", "comp-mips")

# regla -> salida calculada a mano
CASES = {
    "salto_a_la_siguiente": "42\n",      # doble(21)
    "salto_sobre_salto": "4\n",          # break cuando i == 4
    "salto_a_salto": "3\n",              # pares entre 0 y 5: 0, 2, 4
    "fusion_ajustes_sp": "1\n2\n3\n",
    "move_ida_y_vuelta": "6\n",          # gcd(48, 18)
    "identidad_aritmetica": "6\n",       # (2 * 3) + 0
    "carga_tras_guardar": "105\n",       # 100 + 5
    "codigo_muerto": "2\n",              # a[1]
}


@pytest.mark.parametrize("rule", CASES)
def test_demo_triggers_its_rule_and_prints_the_same(rule):
    path = os.path.join(DEMOS, f"17-mirilla-{rule}-valido.cps")
    result = analyze(FileStream(path, encoding="utf-8"))
    assert result["errors"] == []
    assert result["asm_stats"]["peephole"].get(rule, 0) >= 1, result["asm_stats"]["peephole"]

    raw = generate_asm(result["tac"], result["symbol_table_json"]).lines
    optimized, _ = optimize(raw)
    assert len(optimized) < len(raw)
    for lines in (raw, optimized):
        sim = Sim(lines)
        assert sim.run() == CASES[rule]
        assert sim.exit_code == 0
