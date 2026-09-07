# Batería de tests — reglas semánticas

Una carpeta por categoría de regla (mismas categorías del rubro y de
`docs/Arquitectura.md`). Cada regla nueva agrega sus casos en la
carpeta que le corresponde.

Convención sugerida por carpeta:
- `valido_<regla>.cps` — debe analizar sin errores semánticos.
- `invalido_<regla>.cps` — debe producir el/los error(es) que esa regla
  detecta (al menos uno).
- Un `test_<categoria>.py` junto a los `.cps` que llame
  `compiler.analyze_file(...)` sobre cada caso y verifique
  `result["errors"]` vacío o no vacío según corresponda. Ver
  `src/tests/test_smoke.py` para el patrón de `analyze_file` +
  `tmp_path`/rutas relativas.

| Carpeta | Reglas |
|---|---|
| `tipos/` | aritmética, lógicas, comparaciones, asignaciones, const inicializada |
| `ambito/` | resolución de nombres, no declaradas, redeclaración, bloques anidados |
| `funciones/` | argumentos, tipo de retorno, recursión, closures, redeclaración de función |
| `control_flujo/` | condiciones boolean, break/continue en bucles, return en función |
| `clases/` | atributos/métodos por `.`, constructor, `this` |
| `arreglos/` | tipo de elementos, índices |
| `generales/` | código muerto, expresiones sin sentido, declaraciones duplicadas |

Correr todo con:

```
make test
```
