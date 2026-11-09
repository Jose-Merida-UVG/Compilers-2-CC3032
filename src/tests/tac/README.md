# Pruebas de generación de TAC

Una carpeta por área de la rúbrica del Proyecto 2.

| Carpeta | Contenido |
|---|---|
| `declaraciones/` | let/var/const, asignación, print, sombreado |
| `aritmetica/` | + - * / %, precedencia, unario, float mixto, strings |
| `logicas/` | comparaciones, && \|\| ! con cortocircuito, ternario |
| `arreglos/` | literales, indexado, multidimensional, escritura |
| `control_flujo/` | if/else, while, do-while, for, foreach, switch, break/continue |
| `try_catch/` | try/catch simple, anidado, con break/continue/return |
| `funciones/` | parámetros, retorno, void, anidadas, llamadas como argumento, return dentro de try |
| `recursividad/` | factorial, fibonacci, gcd, Hanoi, arreglos, recursión en un método |
| `clases/` | campos, constructor, métodos, `this`, constantes, objetos encadenados |
| `herencia/` | override, método y campo heredados, constructor heredado, tres niveles |
| `temporales/` | reciclaje: picos de temporales, llamadas anidadas, temporales fijados |
| `tabla_simbolos/` | layout: tamaños, offsets, frames, clases (`*.symbols.json`) |

Convención: `valido_<caso>.cps` (debe compilar y generar TAC) e
`invalido_<caso>.cps` (debe dar errores y ningún TAC).

| Archivo | Qué comprueba |
|---|---|
| `test_tac_casos.py` | todos los casos por `analyze()`, el camino real |
| `test_tac_tono.py` | funciones, recursividad, clases, herencia y tabla de símbolos por `compile_tac` |
| `test_tac_invariantes.py` | propiedades de todo TAC válido: `param` antes de cada `call`, aridad, etiquetas, `return` final, pico de temporales |
| `test_cobertura_rubrica.py` | cada fila de la rúbrica tiene área, casos suficientes, construcciones y demos |
| `tabla_simbolos/test_tabla_simbolos.py` | JSON esperado de la tabla de símbolos y reglas de layout |
| `temporales/` | `test_emitter.py`, `test_compile_tac.py`, `test_reciclaje.py` |

Regenerar los `*.symbols.json`: `UPDATE_GOLDEN=1 make test ARGS="src/tests/tac/tabla_simbolos"` y **revisar el diff**.
