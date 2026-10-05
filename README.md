# Compiscript — Compilador: análisis y código intermedio (TAC)

**Demo (Lab 1 — léxico/sintáctico):** https://youtu.be/IowDshTJ0TI

Compilador (front-end) de Compiscript, un lenguaje pequeño similar a un
subconjunto de TypeScript (`let`/`const`/`var`, anotaciones `: type`,
funciones, clases con herencia, arreglos, control de flujo, etc.; la gramática
exacta está en `src/grammar/Compiscript.g4`). Todo el código del compilador vive
en `src/`; `frontend/` es el IDE de navegador (React) que sirve de interfaz
gráfica. Cubre dos entregas del curso:

- **Proyecto 1 — análisis léxico, sintáctico y semántico:** ANTLR4, sistema de
  tipos, tabla de símbolos con manejo de ámbitos y un visitor sobre el árbol de
  análisis.
- **Proyecto 2 — generación de código intermedio:** si el programa no tiene
  ningún error (léxico, sintáctico ni semántico), se genera **código de tres
  direcciones (TAC)** como texto, y la tabla de símbolos se completa con
  tamaños, offsets, direcciones y registros de activación. Si hay cualquier
  error **no se genera TAC**. El compilador no ejecuta el programa ni produce
  código objeto.

Pipeline: `fuente → Lexer → Parser → SemanticChecker → TACGenerator → layout`.

## Documentación

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): panorama con el pipeline, los
  archivos, las herramientas y el reparto del trabajo.
- [docs/semantic.md](docs/semantic.md): Proyecto 1, con el sistema de tipos, la
  tabla de símbolos, el checker, las reglas semánticas, la recuperación de
  errores y las pruebas.
- [docs/tac.md](docs/tac.md): Proyecto 2, con la especificación del lenguaje
  intermedio (instrucciones, justificación, ejemplos fuente → TAC), el algoritmo
  de reciclaje de temporales, la tabla de símbolos para el código objeto, el
  generador, las pruebas y la autoría.
- [docs/enunciados/](docs/enunciados/): definición del lenguaje y requisitos
  del P1.

## Estructura del proyecto

- `src/grammar/Compiscript.g4`: gramática ANTLR4 (fuente de verdad de las reglas del lexer y el parser).
- `src/generated/`: salida de `make generate`; nunca se edita a mano.
- `src/compiler.py`: pipeline compartido (léxico, sintáctico, semántico, generación de TAC y recolección de errores) que usan el CLI y el servidor.
- `src/error_listener.py`: listener de errores de ANTLR que da formato en español a los errores léxicos y sintácticos y permite seguir tras el primer error.
- `src/semantic/`: análisis semántico. `types.py` (sistema de tipos), `symbols.py` (tabla de símbolos y árbol de ámbitos), `errors.py`, `checker.py` (el visitor `SemanticChecker`, con todas las reglas; también anota cada nodo con su tipo y símbolo para la fase de TAC) y `layout.py` (tamaños, offsets, direcciones, registros de activación y layout de clases).
- `src/tac/`: generación de código intermedio. `generator.py` (`TACGenerator`, une los cuatro mixins), `gen_core.py` (declaraciones, expresiones, condiciones, arreglos), `gen_control.py` (if, bucles, switch, try/catch), `gen_functions.py` (funciones, llamadas, return), `gen_classes.py` (clases, objetos, herencia), `emitter.py` (emisión de instrucciones y reciclaje de temporales) e `instructions.py` (convenciones de formato).
- `src/main.py`: punto de entrada del CLI (`make cli`).
- `src/server.py`: backend FastAPI, con una API de archivos sobre `workspace/` y `/api/run`.
- `src/tests/`: pruebas automáticas (`make test`). `src/tests/semantic/<categoría>/` tiene una batería de casos `.cps` por categoría de regla semántica, y `src/tests/tac/<área>/` tiene casos válidos e inválidos por cada punto de la rúbrica de TAC (los válidos deben compilar y generar TAC).
- `src/tools/`: jar de ANTLR incluido, usado solo para generar el código.
- `frontend/`: IDE de navegador (Vite + React/TS). Tiene explorador de archivos (selecciona el archivo de entrada), editor, panel de salida con errores navegables, visor del árbol de análisis, visor de la tabla de símbolos (con tamaños, offsets y registros de activación) y visor de TAC. Todos los resultados se muestran ahí, no solo en consola.
- `workspace/`: directorio de trabajo del IDE. `input/` tiene programas `.cps` de ejemplo (`input/comp-tac/` tiene los demos de la rúbrica del P2) y `output/` guarda los resultados de cada corrida (`.out`, `.tree`, `.symbols`, `.tac`).
- `docs/`: documentación (arquitectura, una guía por proyecto y los enunciados).

## Requisitos

- Java (JRE 11+): solo para ejecutar el jar de ANTLR al generar el código.
- Python 3.9+
- Node.js: solo para el frontend.

## Instalación

```
make install
```

Esto crea un `.venv` en la raíz del repositorio (si no existe), instala en él las
dependencias de Python de `src/requirements.txt` y ejecuta `npm install` en
`frontend/`.

Los targets del Makefile que usan Python (`run`, `cli`) detectan `.venv`
solos: si existen `.venv/bin/python3` y `.venv/bin/uvicorn` los usan, y si no,
usan los `python3` y `uvicorn` del `PATH`. No hace falta hacer
`source .venv/bin/activate`, aunque se puede para tener una shell con el entorno
activo.

El jar de ANTLR ya está incluido en `src/tools/antlr-4.13.2-complete.jar` (solo se
usa para regenerar el parser, no en tiempo de ejecución).

## Generar el parser

Hay que correrlo después de cualquier cambio en `src/grammar/Compiscript.g4`:

```
make generate
```

Esto ejecuta `src/generate.sh`, que invoca el jar de ANTLR y regenera
`CompiscriptLexer.py`, `CompiscriptParser.py`, `CompiscriptVisitor.py` y
`CompiscriptListener.py` en `src/generated/`. Esos archivos son salida de
compilación: no se editan a mano, se edita la gramática y se regenera.

## Ejecutar un archivo (CLI)

```
make cli FILE=<ruta-al-archivo-fuente>
```

Por ejemplo:

```
make cli FILE=workspace/input/comp-tac/funciones-valido.cps
```

Esto hace el análisis léxico y sintáctico del archivo y, si no hubo errores de
esas fases, el análisis semántico. Imprime todos los errores encontrados, en
español y en una sola corrida, seguidos de una línea de estado con el resultado.
Si **no hubo ningún error**, imprime además el código de tres direcciones (TAC)
generado; con cualquier error no se genera TAC.

## Ejecutar las pruebas

```
make test
```

Corre toda la suite de `pytest`:

- `src/tests/semantic/<categoría>/` tiene una batería de casos
  `valido_*.cps`/`invalido_*.cps` por categoría de regla semántica (`tipos`,
  `ambito`, `funciones`, `control_flujo`, `clases`, `arreglos`, `generales`).
- `src/tests/tac/<área>/` tiene una carpeta por punto de la rúbrica de TAC
  (`declaraciones`, `aritmetica`, `logicas`, `arreglos`, `control_flujo`,
  `try_catch`, `funciones`, `recursividad`, `clases`, `herencia`,
  `temporales`, `tabla_simbolos`). Cada `valido_X.cps` debe compilar y generar
  TAC; cada `invalido_X.cps` debe reportar errores y **no** generar TAC. Otras
  pruebas verifican invariantes del TAC (`param` antes de cada `call`,
  etiquetas, reciclaje de temporales, sin fugas) y que cada fila de la rúbrica
  esté cubierta.
- `src/tests/test_smoke.py` y `src/tests/test_analyze.py`: regresiones de la
  gramática y del pipeline.

Para acotarlas: `make test ARGS="src/tests/tac/control_flujo -v"`. Las tablas de
símbolos esperadas (`tabla_simbolos/valido_*.symbols.json`) se regeneran con
`UPDATE_GOLDEN=1 make test ARGS="src/tests/tac/tabla_simbolos"`; hay que
**revisar el diff**.

Los programas de demostración del IDE están en `workspace/input/comp-tac/`: un
`<área>-valido.cps` y un `<área>-invalido.cps` por cada punto de la rúbrica del
Proyecto 2.

## IDE web (frontend y backend juntos)

```
make run
```

Esto inicia el backend FastAPI (`src/server.py`, puerto 8080, con `--reload`) y el
servidor de desarrollo de Vite a la vez, y detiene ambos con Ctrl+C. Se abre la
URL que imprime Vite (por defecto `http://localhost:5173`), que redirige `/api/*`
al backend (ver `frontend/vite.config.ts`).

El backend ofrece una API de archivos sobre `workspace/` (en la raíz del
repositorio, con programas `.cps` de ejemplo en `workspace/input/`) y
`/api/run`, que pasa un archivo por el mismo pipeline que el CLI
(`src/compiler.py`, compartido por ambos) y devuelve los errores, un mensaje de
estado, el árbol de análisis en JSON, la tabla de símbolos en JSON (si corrió el
análisis semántico) y, solo si no hay errores, el TAC y sus estadísticas (`tac`,
`tacStats`) para los visores.

En el IDE: **se elige el archivo de entrada en el explorador lateral** (o se crea
uno nuevo con el botón ＋) y se hace clic en **▶ Compilar**. Todos los resultados
se muestran dentro de la interfaz, no solo en la terminal:

- Los errores (léxicos, sintácticos y semánticos, todos los de esa corrida y no
  solo el primero) y la línea de estado salen en el panel de salida. Cada error
  es clicable y salta a su línea en el editor.
- Se abre solo una pestaña de **árbol de análisis**, con una representación visual
  colapsable del árbol sintáctico.
- Se abre solo una pestaña de **tabla de símbolos** cuando corrió el análisis
  semántico. Muestra cada ámbito (global, función, clase, bloque) anidado como se
  creó, con sus símbolos, tipos y, una vez generado el TAC, tamaño, offset y
  dirección, además del registro de activación de cada función y el layout de
  campos de cada clase.
- Se abre solo una pestaña de **TAC** cuando el programa no tiene errores: el
  código intermedio con numeración de líneas, etiquetas, saltos y temporales
  resaltados, y un botón para copiar. Con cualquier error la pestaña se oculta y
  un aviso indica que no se generó código intermedio.

Cada corrida guarda además en el workspace `output/<nombre>/<nombre>.cps.out`
(texto plano), `.tree` (árbol de análisis en JSON), `.symbols` (tabla de símbolos
en JSON, si corrió el análisis semántico) y `.tac` (el código intermedio, si no
hubo errores; si la nueva corrida tiene errores se borra el `.tac` de la anterior).
Todos se pueden reabrir desde el explorador, y los `.tree` y `.symbols` se abren
en sus visores en vez de como JSON crudo.

## Limpieza

```
make clean       # borra los directorios __pycache__ y workspace/output/
make distclean   # clean, y además borra .venv
```

## Equipo y división de trabajo

La referencia final de quién hizo qué son los commits individuales; esto es el
resumen (detalle en [docs/semantic.md](docs/semantic.md) §10 y
[docs/tac.md](docs/tac.md) §14).

| Integrante | Proyecto 1 (semántico) | Proyecto 2 (código intermedio) |
|---|---|---|
| Camila Richter (`Cami`) | tabla de símbolos y ámbitos | diseño del TAC y reciclaje de temporales (`instructions.py`, `emitter.py`, `generator.py`), anotaciones del checker, integración en `compiler.py`, `main.py` y `server.py`, y la GUI |
| Marinés García (`NESHGP04`) | sistema de tipos y funciones | declaraciones, aritmética, lógicas, arreglos, control de flujo y try/catch (`gen_core.py`, `gen_control.py`) y sus baterías de pruebas |
| Jose Antonio Mérida (`TonitoMC`) | control de flujo, clases, arreglos, IDE | funciones, recursividad, clases y herencia (`gen_functions.py`, `gen_classes.py`), y tabla de símbolos con layout de memoria (`layout.py`, `symbols.py`) |
