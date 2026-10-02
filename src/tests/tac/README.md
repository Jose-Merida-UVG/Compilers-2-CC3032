# Pruebas de generación de TAC

Una carpeta por área de la rúbrica; `test_tac_golden.py` recorre todas.

| Carpeta | Contenido |
|---|---|
| `declaraciones/` | let/var/const, asignación, print, sombreado |
| `aritmetica/` | + - * / %, precedencia, unario, float mixto, strings |
| `logicas/` | comparaciones, && \|\| ! con cortocircuito, ternario |
| `arreglos/` | literales, indexado, multidimensional, escritura, foreach sobre arreglos |
| `control_flujo/` | if/else, while, do-while, for, foreach, switch, break/continue |
| `try_catch/` | try/catch simple, anidado, con break/continue/return |

Convención: `valido_<caso>.cps` + `valido_<caso>.tac` (golden), e
`invalido_<caso>.cps` (debe dar errores y ningún TAC). Regenerar golden:
`UPDATE_GOLDEN=1 make test ARGS="src/tests/tac"` y **revisar el diff**.
