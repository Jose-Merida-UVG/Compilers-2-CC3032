"""Cobertura de la rúbrica del Proyecto 2 (25 pts) contra las pruebas.

Cada fila de la rúbrica se asigna a un área de `src/tests/tac/`. Para cada
área se comprueba que hay al menos 3 casos válidos y 2 inválidos, que entre
los válidos aparecen las construcciones que nombra la rúbrica (en el fuente) y
que el TAC generado contiene las instrucciones esperadas.
"""
import glob
import os
import re

import pytest

from compiler import analyze_file

_HERE = os.path.dirname(os.path.abspath(__file__))
_DEMOS = os.path.join(_HERE, "..", "..", "..", "workspace", "input", "comp-tac")

# área -> (fila de la rúbrica, puntos, patrones en el fuente, texto en el TAC)
RUBRICA = {
    "declaraciones": ("Declaración y asignación de variables y constantes", 1,
                      [r"\blet\b", r"\bvar\b", r"\bconst\b", r"\w+ = "], ["= "]),
    "aritmetica": ("Expresiones aritméticas", 1,
                   [r"\+", r" - ", r"\*", r" / ", r"%"], [" + ", " - ", " * ", " / ", " % "]),
    "logicas": ("Expresiones lógicas", 1,
                [r"&&", r"\|\|", r"!", r"<", r"==", r"\?"], ["goto", "ifFalse"]),
    "arreglos": ("Arreglos", 1,
                 [r"\[\d", r"\[\w+\]", r"\[\["], ["newarray", "["]),
    "control_flujo": ("Sentencias de control", 3,
                      [r"\bif\b", r"\belse\b", r"\bwhile\b", r"\bdo\b", r"\bfor\b",
                       r"\bforeach\b", r"\bswitch\b", r"\bbreak\b", r"\bcontinue\b"],
                      ["goto", "len "]),
    "funciones": ("Funciones y parámetros", 2,
                  [r"\bfunction\b", r"\breturn\b"], ["func ", "param ", "call ", "return"]),
    "recursividad": ("Recursividad", 2, [r"\bfunction\b", r"\breturn\b"], ["call "]),
    "clases": ("Clases y objetos", 2,
               [r"\bclass\b", r"\bnew\b", r"\bthis\b", r"\bconstructor\b"],
               ["class ", "endclass", "= new ", "__init_fields", ".constructor"]),
    "herencia": ("Herencia", 2, [r"\bclass \w+ : \w+"], ["class ", " : ", "call "]),
    "try_catch": ("try y catch", 2, [r"\btry\b", r"\bcatch\b"], ["try L", "endtry", "catch "]),
    "temporales": ("Reciclaje de variables temporales", 3, [r"\+", r"\*"], ["$t1", "$t2"]),
    "tabla_simbolos": ("Nuevas funcionalidades en tabla de símbolos", 2,
                       [r"\bclass\b", r"\bfunction\b"], ["func "]),
}


def _files(area: str, pattern: str) -> list[str]:
    return sorted(glob.glob(os.path.join(_HERE, area, pattern)))


def _read_all(paths: list[str]) -> str:
    out = []
    for path in paths:
        with open(path, encoding="utf-8") as f:
            out.append(f.read())
    return "\n".join(out)


def test_rubric_adds_up_to_25_points():
    # "Diseño del código intermedio" (3 pts) es el documento docs/tac.md
    assert sum(points for _, points, _, _ in RUBRICA.values()) + 3 == 25
    assert os.path.exists(os.path.join(_HERE, "..", "..", "..", "docs", "tac.md"))


@pytest.mark.parametrize("area", RUBRICA)
def test_area_has_enough_cases(area):
    assert len(_files(area, "valido_*.cps")) >= 3, f"{area}: faltan casos válidos"
    assert len(_files(area, "invalido_*.cps")) >= 2, f"{area}: faltan casos inválidos"


@pytest.mark.parametrize("area", RUBRICA)
def test_valid_sources_use_the_rubric_constructs(area):
    _, _, source_patterns, _ = RUBRICA[area]
    sources = _read_all(_files(area, "valido_*.cps"))
    missing = [p for p in source_patterns if not re.search(p, sources)]
    assert not missing, f"{area}: ningún caso válido usa {missing}"


@pytest.mark.parametrize("area", RUBRICA)
def test_generated_tac_contains_the_expected_instructions(area):
    _, _, _, tac_fragments = RUBRICA[area]
    tac = "\n".join(
        "\n".join(analyze_file(path)["tac"]) for path in _files(area, "valido_*.cps")
    )
    missing = [t for t in tac_fragments if t not in tac]
    assert not missing, f"{area}: el TAC no contiene {missing}"


@pytest.mark.parametrize("area", RUBRICA)
def test_area_has_working_demo_files(area):
    """La demo del IDE: un programa válido (con TAC) y uno inválido (sin TAC)."""
    number = f"{list(RUBRICA).index(area) + 1:02d}"  # 01-... en el orden de la rúbrica
    valid = analyze_file(os.path.join(_DEMOS, f"{number}-{area}-valido.cps"))
    assert valid["errors"] == [] and valid["tac"]
    invalid = analyze_file(os.path.join(_DEMOS, f"{number}-{area}-invalido.cps"))
    assert invalid["errors"] and invalid["tac"] is None
