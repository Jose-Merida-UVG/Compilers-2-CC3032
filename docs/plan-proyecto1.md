# Plan de trabajo — Proyecto 1: Análisis Semántico

## Estado

- ✅ **Fase 0 completa** (branch `proyecto1`): gramática extendida con
  `float` (tipo + `FloatLiteral`, regenerada), interfaces acordadas
  implementadas en `src/semantic/` (`types.py`, `symbols.py`, `errors.py`),
  esqueleto de `checker.py` (`SemanticChecker`) conectado a
  `compiler.py` — corre como no-op hoy, cero errores semánticos, cero
  regresión en lo que ya existía. Suite de tests con `pytest` creada
  (`make test`), con carpetas por categoría en `src/tests/semantic/` listas
  para que cada quien agregue sus casos.
- ⏳ Reglas semánticas reales (Personas 1/2/3, ver división abajo):
  pendiente.

## Punto de partida

El lab anterior es la base de este proyecto, no se reinicia nada. La
gramática oficial del proyecto (`compiscript/program/Compiscript.g4` en el
material del curso) es **idéntica** a [`src/grammar/Compiscript.g4`](../src/grammar/Compiscript.g4).
Ya existen lexer, parser, CLI, servidor HTTP y el IDE funcionando sobre esa
gramática.

Lo que **no existe todavía**:
- Analizador semántico (tipos, ámbitos, reglas).
- Tabla de símbolos.
- Suite de tests automatizada (`workspace/input/comp-baja|media` son
  programas de muestra para el IDE, no un test suite — no hay `pytest` ni
  carpeta `tests/` en el repo).

Nota de contexto: el material del curso trae tres fases sobre el mismo
compilador — análisis semántico (este proyecto), generación de código
intermedio (TAC) y generación de código MIPS. Lo que diseñemos ahora, sobre
todo la tabla de símbolos, debe pensarse para no reescribirse en el
proyecto 2.

## Rúbrica (referencia)

| Componente | Puntos |
|---|---|
| IDE | 15 |
| Analizador sintáctico y semántico con validación de reglas semánticas y sistema de tipos | 60 |
| Tabla de símbolos | 25 |
| **Total** | **100** |

Modalidad: grupos de 3. Se validan commits y contribuciones individuales —
no se permite "compartir" commits en conjunto.

## Decisiones técnicas previas

| Decisión | Resolución | Nota |
|---|---|---|
| `float` no existe en la gramática pero la rúbrica lo pide | **Extender la gramática**: agregar `float` a `baseType` y un `FloatLiteral` al lexer (ej. `[0-9]+'.'[0-9]+`), regenerar con `make generate` | Cambio de Fase 0, compartido, antes de repartir el resto — todo lo que dependa del parser generado se ve afectado |
| Listener vs Visitor de ANTLR | **Visitor** (`CompiscriptVisitor`, ya generado) | Cada `visit` devuelve el `Type` del nodo — más natural para propagar tipos que el patrón de callbacks de Listener con pila manual |
| Inferencia de tipo en `let x = 5;` (sin anotación) | El tipo se infiere del `initializer`; sin anotación y sin valor inicial, el símbolo queda con tipo `unknown` que se resuelve con la primera asignación | Confirmar en equipo antes de implementar — afecta a Persona 1 y 2 |
| `null` | Asignable a cualquier tipo referencia (array, clase); no asignable a `integer`/`boolean`/`string`/`float` | Definir explícito para no tener ambigüedad en cada chequeo de asignación |
| Sobrecarga de funciones | **No soportada** — redeclarar un nombre de función en el mismo ámbito es error | Así lo sugiere la rúbrica ("si no se soporta sobrecarga") |
| Idioma de mensajes de error | Español, mismo estilo que [`error_listener.py`](../src/error_listener.py) (línea/columna + descripción) | Consistencia con lo que ya se ve en el IDE |
| Promoción numérica | `integer` se promueve a `float` en aritmética mixta (`1 + 2.5` → `float`); no al revés | Estándar y simple de justificar en la documentación |

## Arquitectura propuesta (nuevo código)

```
src/semantic/
  types.py      # jerarquía de tipos: Integer, Float, Boolean, String, Array(elem),
                #   Function(params, ret), ClassType(name), Null, Void, ErrorType
  symbols.py    # Symbol (nombre, kind, type, declarado-en) + Scope (padre, tabla local)
                #   + SymbolTable (pila de scopes: global → clase/función → bloque)
  errors.py     # SemanticError, lista acumulada (igual patrón que CompiscriptErrorListener)
  checker.py    # SemanticChecker(CompiscriptVisitor) — el recorrido real
```

Integración con lo que ya existe:
- `compiler.py`: después de `parser.program()`, si no hay errores de
  sintaxis (o incluso si los hay, para dar más feedback), correr
  `SemanticChecker().visit(tree)` y agregar sus errores a la lista.
- `server.py`: el endpoint `/api/run` ya devuelve `errors`/`tree` — se le
  suma `symbolTable` (snapshot serializado) para que el IDE la pueda
  mostrar.
- Frontend: nueva pestaña/panel "Tabla de símbolos" junto al
  `ParseTreeViewer` que ya existe — mismo patrón (JSON → árbol/tabla
  colapsable).
- **Tests**: no existe test suite todavía — se crea `src/tests/semantic/`
  con pytest, organizada por categoría de regla (`tipos/`, `ambito/`,
  `funciones/`, `control_flujo/`, `clases/`, `arreglos/`, `generales/`),
  cada una con casos `valido_*.cps` / `invalido_*.cps`. Es un entregable
  explícito de la rúbrica, no opcional.

## División de tareas (3 personas)

La rúbrica separa IDE (15) / Analizador+reglas (60) / Tabla de símbolos
(25), pero repartir así literal deja a una persona bloqueada esperando a
otra (las reglas semánticas *necesitan* la tabla de símbolos para existir).
Mejor repartir por **categorías de reglas**, con la tabla de símbolos como
cimiento que hace una persona primero y las otras dos consumen.

**Fase 0 (conjunta, ~1 sesión):** extender gramática con `float`,
regenerar, y acordar en código real la interfaz de `Type`/`Symbol`/`Scope`
que todos van a usar. No hay commits individuales limpios posibles si esto
no se acuerda primero.

### Persona 1 — Fundamentos: Tabla de Símbolos + Tipos + Ámbito
*(25 pts de tabla + parte del bloque de ámbito)*
- `symbols.py`, `types.py` — diseño y implementación.
- Reglas de **Manejo de Ámbito**: resolución de nombres, uso de variable no
  declarada, redeclaración prohibida, nuevo entorno por función/clase/
  bloque, acceso correcto en bloques anidados.
- Debe entregar su API (aunque sea incompleta) primero — las otras dos
  personas la importan desde el día 2.

### Persona 2 — Tipos en expresiones + Funciones
- **Sistema de Tipos**: aritmética, lógica, comparaciones, asignaciones,
  const inicializada obligatoriamente.
- **Funciones**: número/tipo de argumentos (posicional), tipo de retorno,
  recursión, funciones anidadas/closures (captura de entorno),
  redeclaración de función con mismo nombre.
- Generales relacionado: expresiones sin sentido semántico (ej. multiplicar
  una función).

### Persona 3 — Control de flujo + Clases + Arreglos + IDE
- **Control de flujo**: condiciones `boolean` en
  `if/while/do-while/for/switch`, `break`/`continue` solo en bucles,
  `return` solo dentro de función.
- **Clases y objetos**: atributos/métodos válidos vía `.`, constructor,
  `this`.
- **Listas**: tipo de elementos, validación de índices.
- Generales: código muerto, declaraciones duplicadas de variables/
  parámetros.
- Dueño de la **integración al IDE** (endpoint + panel de tabla de símbolos
  en el frontend) — es quien ya conoce ese flujo end-to-end.

Tests: cada quien escribe la batería de su propia categoría (reparte el
trabajo de pruebas de forma natural y deja autoría clara en los commits,
como pide la rúbrica). Documentación: cada quien documenta su módulo; una
persona arma el documento consolidado de arquitectura al final.

## Orden sugerido

1. ✅ Fase 0 conjunta: gramática `float` + interfaces de `types.py`/
   `symbols.py` acordadas e implementadas (`src/semantic/`), esqueleto de
   `checker.py` conectado a `compiler.py`, suite de tests con `pytest`
   (`make test`).
2. Persona 1 implementa la tabla de símbolos real esta primera semana
   (rellenar los métodos marcados `TODO(Persona 1)` en
   `src/semantic/checker.py`); Personas 2 y 3 mientras tanto escriben sus
   visitors contra la interfaz acordada, con mocks si hace falta.
3. Integración continua: cada quien va llenando los métodos ya presentes
   en `SemanticChecker` (uno por regla, agrupados y comentados por dueño en
   `checker.py`) — no hace falta rediseñar el esqueleto, solo reemplazar
   cada `TODO` por la lógica real.
4. Tests + integración al IDE en paralelo, al final.
5. Documentación de arquitectura.

## Fase 0 — qué quedó y cómo usarlo

- `src/grammar/Compiscript.g4`: `baseType` ahora incluye `'float'`;
  `Literal` incluye `FloatLiteral` (`[0-9]+ '.' [0-9]+`). Regenerado con
  `make generate`.
- `src/semantic/types.py`: jerarquía de `Type` (`IntegerType`, `FloatType`,
  `BooleanType`, `StringType`, `ArrayType`, `FunctionType`, `ClassType`,
  `NullType`, `VoidType`, `UnknownType`, `ErrorType`) con
  `is_assignable_to` implementando las reglas de la tabla de decisiones de
  arriba (promoción integer→float, null a tipos referencia, ErrorType
  absorbe todo para no cascadear errores).
- `src/semantic/symbols.py`: `Symbol`, `Scope` (con `declare`,
  `resolve_local`, `resolve`, `enclosing(kind)`), `SymbolTable` (pila de
  scopes: `enter_scope`/`exit_scope`/`current`). `Symbol.address` existe
  pero se queda en `None` hasta la fase de TAC/MIPS.
- `src/semantic/errors.py`: `SemanticError`/`SemanticErrorList`, mismo
  formato en español que `error_listener.py`.
- `src/semantic/checker.py`: `SemanticChecker(CompiscriptVisitor)` — un
  método `visit*` por regla relevante, cada uno con un comentario
  `TODO(Persona N): ...` explicando qué debe hacer y con quién coordinar.
  Hoy todos hacen `return self.visitChildren(ctx)` (no-op idéntico al
  default heredado) — es el punto de partida para llenar la lógica real.
- `src/compiler.py`: `analyze()` corre `SemanticChecker().check(tree)`
  **solo si no hubo errores léxicos/sintácticos** (recorrer un árbol con
  recuperación de errores de ANTLR produciría ruido semántico engañoso).
- `src/tests/`: `conftest.py` deja `import compiler`, `from semantic...`
  funcionando desde cualquier test; `test_smoke.py` es el guardia de
  regresión de la Fase 0 (todas las muestras de `workspace/input/` más el
  literal `float`); `semantic/<categoria>/` son las carpetas donde cada
  quien agrega su batería — ver `src/tests/semantic/README.md`.
- Correr todo: `make test`.
