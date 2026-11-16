# Compiscript — Compilador: análisis, código intermedio (TAC) y MIPS

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
  error **no se genera TAC**.
- **Proyecto 3 — código objeto:** con el TAC y la tabla de símbolos se genera
  ensamblador **MIPS32** (para MARS/SPIM), con asignación de registros,
  registros de activación, objetos con despacho dinámico y excepciones. Si hay
  cualquier error no se genera MIPS. El compilador no ejecuta el programa.

Pipeline: `fuente → Lexer → Parser → SemanticChecker → TACGenerator → layout → generador de MIPS`.

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
- [Código objeto (MIPS)](#código-objeto-mips), más abajo en este README: Proyecto 3, con el
  IR, el modelo de memoria, el asignador de registros, los selectores, el runtime, la
  mirilla y un ejemplo recorrido.
- [docs/enunciados/](docs/enunciados/): definición del lenguaje y requisitos
  del P1.

## Estructura del proyecto

- `src/grammar/Compiscript.g4`: gramática ANTLR4 (fuente de verdad de las reglas del lexer y el parser).
- `src/generated/`: salida de `make generate`; nunca se edita a mano.
- `src/compiler.py`: pipeline compartido (léxico, sintáctico, semántico, generación de TAC y recolección de errores) que usan el CLI y el servidor.
- `src/error_listener.py`: listener de errores de ANTLR que da formato en español a los errores léxicos y sintácticos y permite seguir tras el primer error.
- `src/semantic/`: análisis semántico. `types.py` (sistema de tipos), `symbols.py` (tabla de símbolos y árbol de ámbitos), `errors.py`, `checker.py` (el visitor `SemanticChecker`, con todas las reglas; también anota cada nodo con su tipo y símbolo para la fase de TAC) y `layout.py` (tamaños, offsets, direcciones, registros de activación y layout de clases).
- `src/tac/`: generación de código intermedio. `generator.py` (`TACGenerator`, une los cuatro mixins), `gen_core.py` (declaraciones, expresiones, condiciones, arreglos), `gen_control.py` (if, bucles, switch, try/catch), `gen_functions.py` (funciones, llamadas, return), `gen_classes.py` (clases, objetos, herencia), `emitter.py` (emisión de instrucciones y reciclaje de temporales) e `instructions.py` (convenciones de formato).
- `src/asm/`: generación de MIPS. `ir/` (el IR: tipos, operandos e instrucciones), `tac_parser.py` (TAC texto → IR), `frames.py` (marcos de activación), `regalloc.py` (asignador de registros), `sel_*.py` (los selectores, agrupados por tema: asignación, operaciones, control, arreglos, llamadas, objetos, excepciones), `runtime.py`/`runtime_exc.py` (rutinas y excepciones), `peephole.py` (mirilla), `activation.py` (datos del IDE), `emitter.py` y `generator.py` (el driver). Ver [Código objeto (MIPS)](#código-objeto-mips).
- `src/main.py`: punto de entrada del CLI (`make cli`).
- `src/server.py`: backend FastAPI, con una API de archivos sobre `workspace/` y `/api/run`.
- `src/tests/`: pruebas automáticas (`make test`). `src/tests/semantic/<categoría>/` tiene una batería de casos `.cps` por categoría de regla semántica, y `src/tests/tac/<área>/` tiene casos válidos e inválidos por cada punto de la rúbrica de TAC (los válidos deben compilar y generar TAC).
- `src/tools/`: jar de ANTLR incluido, usado solo para generar el código.
- `frontend/`: IDE de navegador (Vite + React/TS). Tiene explorador de archivos (selecciona el archivo de entrada), editor, panel de salida con errores navegables, visor del árbol de análisis, visor de la tabla de símbolos (con tamaños, offsets y registros de activación) y visor de TAC. Todos los resultados se muestran ahí, no solo en consola.
- `workspace/`: directorio de trabajo del IDE. `input/` tiene programas `.cps` de ejemplo (`input/comp-mips/` tiene los demos del IDE: los de la rúbrica del P2 y los de MIPS) y `output/` guarda el código generado de cada corrida (`.tac` y `.s`).
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
make cli FILE=workspace/input/comp-mips/06-funciones-valido.cps
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

Los programas de demostración del IDE están en `workspace/input/comp-mips/`: un
`NN-<área>-valido.cps` y un `NN-<área>-invalido.cps` por cada punto de la rúbrica del
Proyecto 2, numerados en el orden de la rúbrica (01 a 12), `13-recorrido-completo.cps`,
una demo que junta todas las áreas, y dos del Proyecto 3: `14-registros` (muchos valores
vivos, el asignador derrama a memoria) y `15-activacion` (llamadas anidadas, recursión y un
método, para el árbol y los registros de activación). `make test` compila todos a MIPS y
los ejecuta.

## Ejecutar el MIPS

```
make mips FILE=workspace/input/comp-mips/15-activacion-valido.cps
```

Compila el `.cps` a MIPS y lo ejecuta en MARS, imprimiendo lo que imprime el
programa (`--save salida.s` en `src/run_mips.py` guarda además el ensamblador). Con
errores no ejecuta nada. Necesita `java` y `Mars4_5.jar` (`MARS_JAR` o
`src/tools/`). En el IDE se hace con **▶ Ejecutar**.

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

Cada corrida guarda el código generado en `output/<nombre>/`: `<nombre>.cps.tac` (el
código intermedio) y `<nombre>.cps.s` (el MIPS), solo si no hubo errores; con errores se
borran los de la corrida anterior. El árbol, la tabla de símbolos y el resto salen en
sus pestañas, no en archivos.

**▶ Ejecutar** compila el archivo y corre el MIPS en MARS: lo que imprime el programa
sale en el panel OUTPUT, y un programa que no termina se corta a los 10 s. Necesita
`java` y `Mars4_5.jar` en el servidor (`MARS_JAR` o `src/tools/`).

## Limpieza

```
make clean       # borra los directorios __pycache__ y workspace/output/
make distclean   # clean, y además borra .venv
```

## Código objeto (MIPS)

Traduce el TAC (texto) y la tabla de símbolos del P2 a ensamblador MIPS32 para
MARS/SPIM. Vive en `src/asm/`; la entrada es `generate_asm(tac, symbol_table)`
(`generator.py`) y la llama `compiler.analyze()` solo si no hubo ningún error.
Si el generador falla, el error se reporta como "Error interno al generar el
ensamblador" y no se publica ni TAC ni MIPS.

**Dónde leer el código:** el docstring de `src/asm/__init__.py` es la guía
general: define el vocabulario (IR, selector, casa, bloque, flush) y lista los
archivos en el orden en que conviene leerlos. Cada archivo explica su parte en
su propio docstring.

### Flujo

```
TAC (texto) + tabla de símbolos (JSON)
   │  tac_parser.parse_tac         texto → objetos del IR (Program)
   ▼
   │  por cada función:
   │    split_blocks + block_live_out    bloques básicos y temporales vivos
   │    por cada instrucción:  generator._dispatch  →  sel_<Clase>(ins)
   ▼                                   │ el selector pide registros a RegAlloc
MIPS crudo + datos de activación       ▼ y escribe con AsmEmitter
   │  peephole.optimize (opcional)
   ▼
MIPS final
```

### Orden de dependencias (de abajo hacia arriba)

Cada nivel solo importa de los anteriores.

| Nivel | Archivo | Rol |
|---|---|---|
| 0 | `ir/` | El vocabulario: tipos, operandos e instrucciones como objetos (IR). |
| 0 | `emitter.py` | Acumula `.text` y `.data`: `ins`, `label`, `string`, `float_`, `new_label`; nombres seguros (`f_Animal__hablar`, `vt_Animal`). |
| 1 | `tac_parser.py` | TAC texto → `Program` del IR; resuelve tipos, offsets de campos y tamaños con la tabla de símbolos. |
| 1 | `frames.py` | Dónde vive cada valor (`home`) y el prólogo/epílogo de cada función. |
| 1 | `regalloc.py` | `getReg`: qué valor ocupa qué registro en cada momento (asignador). |
| 2 | `sel_*.py` | Selectores: un método por clase de instrucción (selectores). |
| 2 | `runtime.py` | Rutinas en MIPS: `print`, `rt_alloc`, arreglos, strings. |
| 3 | `generator.py` | El driver: recorre el IR y despacha a los selectores. |

### El IR (`ir/`)

Cada línea del TAC es un objeto. Tres capas:

- **`Ty`** (`types.py`): tipo estático de un valor. Elige la instrucción MIPS:
  `addu` / `add.s` / `rt_str_concat`, `lw` / `lwc1` / `lb`.

  | `kind` | Valor | En memoria |
  |---|---|---|
  | `int`, `bool`, `float` | escalares | palabra (el `bool` ocupa 1 byte en su casa; el `float` va en registros `$f`) |
  | `str` | string | puntero a `.asciiz` |
  | `array` (`elem`) | arreglo | puntero a `[longitud][e0][e1]…` |
  | `obj` (`cls`) | instancia | puntero a `[tabla de métodos][campo0]…` |
  | `vtable` | tabla de métodos de un objeto | puntero a la lista de métodos |
  | `null`, `void`, `unknown` | marcadores | `null` es 0 |

- **`Operand`** (`operands.py`): un valor concreto del TAC. Tiene `text` (tal
  cual en el TAC; también es su identidad en el asignador, `key`), `kind`
  (`var` con casa en memoria, `temp` que muere tras su último uso, `const` sin
  casa), `ty`, y `value` solo para constantes (`None` en var/temp; `null` también
  es `None`, así que se revisa `is_const` primero).
- **`Instr`** (`base.py` y los demás módulos): una clase por instrucción del TAC,
  con operandos como campos. Cada una declara en `READS` y `WRITES` los nombres de
  los campos que lee y escribe (`READS = ("a", "b")`); la base deriva de ahí
  `reads()` y `writes()`, que el asignador usa para calcular el siguiente uso, y
  `non_const` descarta constantes y `None`. `line` guarda el TAC original, que se
  emite como comentario.

Ejemplo: `$t1 = b * 2` →
`Binary(dst=$t1:temp:int, a=b:var:int, op="*", b=2:const:int, line="$t1 = b * 2")`.

No toda línea es una instrucción: los `param` se pliegan en el `Call` que
sigue, y `func`/`class`/`vtable` forman las unidades `FuncUnit`, `ClassUnit` y
`Program` (`units.py`).

| Módulo | Contenido |
|---|---|
| `types.py` | `Ty`, `INT`, `FLOAT`, …, `array_of`, `obj_of` |
| `operands.py` | `Operand` |
| `base.py` | `Instr`, `non_const` |
| `control.py` | `Label`, `Goto`, `CondJump`, `Return`, `TERMINATORS` |
| `values.py` | `Copy`, `Unary`, `Binary`, `Print` |
| `arrays.py` | `NewArray`, `Len`, `IndexLoad`, `IndexStore` |
| `objects.py` | `FieldLoad`, `FieldStore`, `New`, `VTableLoad`, `VTableSlotLoad` |
| `calls.py` | `Call`, `CallVirt` |
| `exceptions.py` | `Try`, `EndTry`, `Catch` |
| `units.py` | `FuncUnit`, `ClassUnit`, `Program` |

`ir/__init__.py` reexporta todo, así que se importa siempre `from asm.ir import …`.

### Modelo de memoria

Registro de activación (`frames.py`); la pila crece hacia abajo:

```
fp+8+4*i   argumento i (i = 0 es `this` en un método)
fp+4       $ra guardado
fp+0       $fp del llamador            <- $fp apunta aquí
fp-4 …     locales
debajo     temporales $t1, $t2, … (4 bytes cada uno)
```

- Toda variable y temporal tiene una **casa** fija en memoria, `N($fp)` o
  `N($gp)` (globales); sale de las direcciones que calcula `semantic/layout.py`.
  Nada se direcciona relativo a `$sp`, así que empujar argumentos no invalida
  casas.
- **Llamada**: `addiu $sp,-4n`, `sw` de cada argumento a `4*i($sp)`, `flush`,
  `jal`, `invalidate`, se libera la pila. Retorno en `$v0` (o `$f0` si es float).
- **Heap**: `rt_alloc` (`$a0` = bytes, devuelve `$v0`, memoria en cero).
  Arreglo: `[n][e0]…` con 4 bytes por elemento; la lectura verifica rango y
  salta a `rt_throw_index`.
- **Objeto**: `[tabla de métodos][campos]`; los campos empiezan en el offset 4.
  **Tabla de métodos** (`vt_<Clase>` en `.data`): una palabra por slot con la
  dirección del método; un método sobrescrito reutiliza el slot del padre. Una
  llamada a método es `x = vtable obj` (lee la palabra 0), `$t = $t[slot]`
  (lee el slot, sin cabecera ni verificación de rango) y `callvirt`.

#### Secuencia de llamada y retorno

Estado de la pila para `f(a, b)` (crece hacia abajo; `$fp` fija el marco):

```
 llamador, antes del jal           dentro de f, tras el prólogo
 ┌──────────────┐                  ┌──────────────┐
 │  ...         │                  │  ...         │
 ├──────────────┤ ← $sp+8   fp+12  │  b           │  argumento 1
 │  b           │                  │  a           │  fp+8   argumento 0
 │  a           │ ← $sp     fp+4   │  $ra         │
 └──────────────┘           fp+0   │  $fp viejo   │ ← $fp
                                    │  locales     │  fp-4 …
                                    │  temporales  │
                                    └──────────────┘ ← $sp
```

1. **Llamador:** `addiu $sp,-8`; `sw` de cada argumento a `4*i($sp)`; `flush` (todo lo
   sucio y vivo a su casa); `jal f`; `invalidate`; `addiu $sp,+8`; copia `$v0`/`$f0`.
2. **Prólogo:** `addiu $sp,-8`; guarda `$ra` y `$fp`; `$fp = $sp`; reserva locales y
   temporales (`addiu $sp,-alloc`).
3. **Epílogo:** `$sp = $fp`; restaura `$ra` y `$fp`; `addiu $sp,+8`; `jr $ra`.

El llamado nunca guarda registros: como todo se guarda a su casa antes del `jal`, el
llamador no espera nada en ellos al volver.

### Asignador de registros (`regalloc.py`)

El algoritmo de Aho §8.6.3: un descriptor de registros (qué valor tiene cada
uno), uno de direcciones (dónde está cada valor) y el **siguiente uso**
calculado hacia atrás en cada bloque. Un temporal sin siguiente uso está muerto:
libera su registro y no se guarda; las variables nunca mueren. Pool: `$t0-$t9` y
`$f4, $f6, $f8, $f10, $f14, $f16, $f18` (`$f12` queda reservado). Política *caller-saved*: todo lo sucio y vivo se guarda a su
casa antes de cada salto y de cada `jal`; después de una etiqueta o llamada no se
confía en ningún registro. Los registros ABI `$a0-$a3`, `$v0`, `$v1`, `$f0`,
`$f12` y `$at` nunca se entregan: los selectores los usan a mano.

| Método | Qué hace |
|---|---|
| `use(op)` | Registro con el valor de `op`; lo carga de su casa si hace falta. |
| `def_(op)` | Registro para un resultado; puede reutilizar el de un fuente ya muerto. |
| `scratch()` | Registro anónimo hasta el fin de la instrucción. |
| `into(reg, op)` | Deja `op` en un registro fijo (`$a0`, `$f12`, …). |
| `flush()` | Guarda a su casa lo sucio y vivo. |
| `invalidate()` | Olvida todos los registros (tras `jal`). |

Reglas: pedir los fuentes con `use` antes del destino con `def_` (puede devolver
el mismo registro que un fuente muerto; `avoid=` lo evita); no nombrar registros
para valores; las rutinas del runtime solo tocan registros reservados, así que
se pueden llamar a mitad de una instrucción sin `flush`. Cada decisión queda en
`regs.trace`.

### Selectores (`sel_*.py`)

Un *selector* decide qué instrucciones MIPS emitir para una instrucción del TAC.
El driver busca el método `sel_<NombreDeClase>` (`sel_Binary`, `sel_Call`, …) y
lo llama con el objeto del IR. Un selector típico (`sel_Copy`):

```python
rs = regs.use(src)
rd = regs.def_(dst)
if rd != rs: asm.ins(f"move  {rd}, {rs}")
```

Los selectores son *mixins*: `AsmGenerator` los junta. Si falta un `sel_X`, el
driver falla con `falta el selector sel_X`. El driver antepone un `flush` a
`Return`, `Goto` y `CondJump`, y vacía los registros al entrar a cada bloque.

| Archivo | Instrucciones |
|---|---|
| `sel_core.py` | `Copy` |
| `sel_ops.py` | `Unary`, `Binary`, `Print` (enteros, floats, strings) |
| `sel_control.py` | `Goto`, `CondJump` |
| `sel_arrays.py` | `NewArray`, `Len`, `IndexLoad`, `IndexStore` |
| `sel_calls.py` | `Call`, `Return` |
| `sel_objects.py` | `New`, `FieldLoad`, `FieldStore`, `VTableLoad`, `VTableSlotLoad`, `CallVirt`, y `emit_vtables`; verifican `null` antes de usar un objeto |
| `sel_try.py` | `Try`, `EndTry`, `Catch` |
| `runtime_exc.py` | pila de manejadores, `rt_throw`, `rt_throw_index`, `rt_throw_null` |
| `peephole.py` | `optimize(lines)`: mirilla (8 reglas) sobre el MIPS ya generado |
| `activation.py` | `build_activation(program, frames)`: registros de activación y árbol de llamadas para el IDE |

El driver importa con respaldo los módulos que faltan (clase vacía); un programa
que use una instrucción sin selector falla con el mensaje de arriba.

#### Excepciones

`try L` apila `[dirección de L][$sp][$fp]` en una pila de manejadores en `.data`
(`rt_try_push`); `endtry` la desapila. `rt_throw` (mensaje en `$a0`) restaura
`$sp` y `$fp` del manejador de arriba y salta a `L`, donde `catch e` copia el
mensaje a `e`. Sin manejador imprime `Excepcion no capturada: <mensaje>` y termina
con código 1. Lanzan: el índice fuera de rango (`indice fuera de rango`) y el
acceso a un campo o método de `null` (`referencia nula`). No hay que restaurar
registros al desenrollar porque todo se guarda a su casa antes de cada llamada.

En un programa que usa `try`, `TrySel._dispatch` guarda cada resultado a su casa al
terminar la instrucción: si algo lanza a mitad de un bloque, el manejador (que
empieza con los registros vacíos) lee valores al día de memoria.

#### Mirilla (`peephole.py`)

`optimize(lines)` recibe el MIPS ya generado y lo recorre buscando patrones entre
instrucciones contiguas. Los comentarios `# TAC: ...` y las líneas en blanco se
saltan; las etiquetas **no**, porque alguien puede saltar a ellas. Repite hasta
5 pasadas, porque quitar una instrucción puede dejar otro patrón al descubierto, y
devuelve las líneas nuevas y cuántas veces se aplicó cada regla (el IDE lo muestra).

| Regla | Antes | Después |
|---|---|---|
| `move_redundante` | `move $r, $r` | se quita |
| `salto_a_la_siguiente` | `j L` justo antes de `L:` (puede haber otras etiquetas en medio) | se quita el salto |
| `carga_tras_guardar` | `sw $r, A` + `lw $r, A` (igual con `swc1`/`lwc1`) | se quita el `lw`; `lb` no, porque extiende el signo |
| `guardar_tras_cargar` | `lw $r, A` + `sw $r, A` | se quita el `sw`; no aplica si `$r` es la base de `A` (`lw $t0, 0($t0)` cambia la dirección) |
| `identidad_aritmetica` | `addiu $r,$r,0`, `addu $r,$r,$zero`, `sll $r,$r,0`, `ori $r,$r,0` | se quita (el destino debe ser el mismo registro) |
| `move_ida_y_vuelta` | `move a, b` + `move b, a` | se quita el segundo |
| `salto_sobre_salto` | `beq x,y,L1` + `j L2` + `L1:` | `bne x,y,L2` + `L1:` (y `bne` → `beq`); `L1` debe ser el destino del salto condicional |
| `codigo_muerto` | instrucciones entre un `j`/`jr` y la siguiente etiqueta o directiva | se quitan (nadie puede llegar a ellas) |

Ejemplo (`salto_sobre_salto`, que sale de un `if` cuyo cuerpo termina en `break`):

```
    beq   $t0, $zero, L1          bne   $t0, $zero, L2
    j     L2                 →  L1:
L1:
```

Ninguna regla cambia lo que hace el programa: `test_asm_peephole.py` prueba cada
una (y los casos donde no deben aplicar) y que todos los programas válidos de
`src/tests/asm/` impriman lo mismo con y sin mirilla.

#### Datos del IDE (`activation.py`)

`activation.build_activation` arma los marcos (`FrameInfo.slots()`) y el árbol de
llamadas desplegado desde `__main`, con las llamadas recursivas y virtuales
marcadas.

### Por qué *caller-saved* y sin `$s`

El asignador no usa los registros `$s`: antes de cada salto y de cada `jal` guarda a su
casa todo lo sucio y vivo, y después de una etiqueta o llamada empieza con los registros
vacíos. Es más simple de demostrar correcto (el estado en memoria siempre está al día en
los puntos de control) y hace seguro el `try/catch`: `rt_throw` desenrolla la pila sin
restaurar registros, porque no hay ninguno que restaurar. El costo es más `sw`/`lw` en los
límites de bloque; la mirilla recupera una parte.

### Ejemplo recorrido

```
function cuad(n: integer): integer { return n * n; }
let x: integer = cuad(3) + 1;
print(x);
```

TAC:

```
func cuad(n):                 func __main():
    $t1 = n * n                   param 3
    return $t1                    $t1 = call cuad, 1
endfunc                           $t1 = $t1 + 1
                                  x = $t1
                                  print x
                              endfunc
```

Decisiones de `getReg` (`regs.trace`, lo que muestra el IDE):

| Instrucción TAC | Valor | Registro | Razón |
|---|---|---|---|
| `$t1 = n * n` | `n` | `$t0` | carga (de `8($fp)`) |
| | `$t1` | `$t1` | libre |
| `$t1 = call cuad, 1` | `$t1` | `$t0` | libre (la llamada invalidó todo) |
| `$t1 = $t1 + 1` | `$t1` | `$t0` | mismo registro |
| `x = $t1` | `x` | `$t0` | reuso (`$t1` murió aquí) |

MIPS (sin el prólogo/epílogo, ver arriba):

```
f_cuad:   lw    $t0, 8($fp)          # n es el argumento 0
          mul   $t1, $t0, $t0
          move  $v0, $t1             # return
f___main: li    $v1, 3               # las constantes pasan por $v1, no gastan un registro
          addiu $sp, $sp, -4         # (el marco del llamador ya está armado)
          sw    $v1, 0($sp)
          jal   f_cuad
          addiu $sp, $sp, 4
          move  $t0, $v0             # $t1 vive en $t0
          addiu $t0, $t0, 1          # $t0 = $t0 + 1: el destino reutiliza el fuente
          move  $a0, $t0             # print x
          jal   rt_print_int
          sw    $t0, 0($gp)          # x se guarda a su casa (global: $gp+0) al cerrar
```

(El orden exacto de las líneas se puede ver en la pestaña **asm** del IDE o con
`make mips FILE=... --save`.)

### Limitaciones conocidas

- **Variables capturadas por una función anidada** viven en una casilla fija de `$gp`
  (no en el marco). Funciona con una sola activación de la función exterior, pero si esta
  es recursiva todas las activaciones comparten la variable.
- **División entre cero** no lanza excepción: el resultado de `div` es indefinido en MIPS.
  Sí lanzan `indice fuera de rango` y `referencia nula`.
- **Sin `$s`**: ver arriba. Más tráfico a memoria en los límites de bloque.
- Los literales de arreglo con elementos de subclases distintas (`[new Perro(), new Gato()]`)
  los rechaza el análisis semántico (P1) aunque el tipo declarado sea `Animal[]`.

### Pruebas

`src/tests/asm/<categoría>/`: casos `.cps` con su salida esperada `.out`, un
simulador mínimo (`support/minisim.py`) y pruebas del parser, de los marcos y de
`getReg` (`registros/`). `make test` los corre junto al resto. Las carpetas
`clases/`, `herencia/` y `try_catch/` cubren los objetos y las excepciones;
`test_asm_excepciones.py` las excepciones sin manejador, `test_asm_peephole.py` la
mirilla (cada regla y que optimizar no cambie la salida) y `test_asm_activation.py`
los datos del IDE. Si hay `Mars4_5.jar` (`MARS_JAR` o `src/tools/`) los mismos
casos corren también en MARS real.

## Equipo y división de trabajo

La referencia final de quién hizo qué son los commits individuales; esto es el
resumen (detalle en [docs/semantic.md](docs/semantic.md) §10 y
[docs/tac.md](docs/tac.md) §14).

| Integrante | Proyecto 1 (semántico) | Proyecto 2 (código intermedio) |
|---|---|---|
| Camila Richter (`Cami`) | tabla de símbolos y ámbitos | diseño del TAC y reciclaje de temporales (`instructions.py`, `emitter.py`, `generator.py`), anotaciones del checker, integración en `compiler.py`, `main.py` y `server.py`, y la GUI |
| Marinés García (`NESHGP04`) | sistema de tipos y funciones | declaraciones, aritmética, lógicas, arreglos, control de flujo y try/catch (`gen_core.py`, `gen_control.py`) y sus baterías de pruebas |
| Jose Antonio Mérida (`TonitoMC`) | control de flujo, clases, arreglos, IDE | funciones, recursividad, clases y herencia (`gen_functions.py`, `gen_classes.py`), y tabla de símbolos con layout de memoria (`layout.py`, `symbols.py`) |
