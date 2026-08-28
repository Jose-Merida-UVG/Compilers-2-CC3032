# Batería de tests — reglas semánticas

Una carpeta por categoría de regla (mismas categorías del rubro y de
`docs/plan-proyecto1.md`). Cada quien agrega sus casos en la carpeta que le
corresponde por [docs/plan-proyecto1.md](../../../docs/plan-proyecto1.md).

Convención sugerida por carpeta:
- `valido_<regla>.cps` — debe analizar sin errores semánticos.
- `invalido_<regla>.cps` — debe producir el/los error(es) que esa regla
  detecta (al menos uno).
- Un `test_<categoria>.py` junto a los `.cps` que llame
  `compiler.analyze_file(...)` sobre cada caso y verifique
  `result["errors"]` vacío o no vacío según corresponda. Ver
  `src/tests/test_smoke.py` para el patrón de `analyze_file` +
  `tmp_path`/rutas relativas.

| Carpeta | Reglas | Dueño |
|---|---|---|
| `tipos/` | aritmética, lógicas, comparaciones, asignaciones, const inicializada | Persona 2 |
| `ambito/` | resolución de nombres, no declaradas, redeclaración, bloques anidados | Persona 1 |
| `funciones/` | argumentos, tipo de retorno, recursión, closures, redeclaración de función | Persona 2 |
| `control_flujo/` | condiciones boolean, break/continue en bucles, return en función | Persona 3 |
| `clases/` | atributos/métodos por `.`, constructor, `this` | Persona 3 |
| `arreglos/` | tipo de elementos, índices | Persona 3 |
| `generales/` | código muerto, expresiones sin sentido, declaraciones duplicadas | Persona 2 / 3 (repartir al llegar) |

Correr todo con:

```
make test
```
