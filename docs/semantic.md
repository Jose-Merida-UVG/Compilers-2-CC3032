# Análisis semántico (Proyecto 1)

Diseño interno de `src/semantic/` y del checker: sistema de tipos, tabla de
símbolos, reglas implementadas, recuperación de errores y pruebas. El enunciado
está en [`enunciados/SemanticAnalysis.md`](enunciados/SemanticAnalysis.md); el
panorama del pipeline completo, en [`ARCHITECTURE.md`](ARCHITECTURE.md); la
generación de código intermedio (P2), en [`tac.md`](tac.md).

## 1. Sistema de tipos (`types.py`)

Toda expresión evalúa a una instancia de `Type`, y todo método `visit` que
maneje una expresión devuelve una (ver §3.1).

- **Primitivos**: `BooleanType`, `IntegerType`, `FloatType`, `StringType`.
- **Compuestos**: `ArrayType(element)`, `FunctionType(params, ret)`,
  `ClassType(name, parent, members)`.
- **De maquinaria**, sin equivalente en el lenguaje fuente:
  - **`UnknownType`**: "todavía no se sabe". Lo producen `let x;` sin anotación
    ni inicializador, un parámetro sin `: type` y `[]`. Acepta cualquier valor y
    se fija con la primera asignación (el símbolo actualiza su `type`).
  - **`ErrorType`**: "ya se rompió y ya se reportó". Se devuelve tras reportar
    un error y es compatible con cualquier tipo en ambas direcciones, para que
    una subexpresión inválida no dispare errores derivados en cada nodo que la
    contiene.
  - **`VoidType`** (retorno de una función sin anotación) y **`NullType`**.

Toda la política de compatibilidad vive en `Type.is_assignable_to(target)`: "¿un
valor de este tipo cabe donde se espera `target`?". El caso base es igualdad
estructural (el checker crea instancias nuevas en cada punto, así que `__eq__`
compara por estructura; `ClassType` compara por nombre). Las subclases la
relajan:

| Tipo | Regla adicional |
|---|---|
| `IntegerType` | también cabe en `FloatType` (promoción, nunca al revés) |
| `NullType` | cabe en arreglos y clases, nunca en primitivos |
| `ClassType` | cabe en cualquier ancestro (`is_subclass_of`) |
| `ArrayType` | invariante para tipos reales; permeable a `Unknown`/`Error` a cualquier profundidad (`_element_fits`) |
| `Unknown` / `Error` | aceptan todo en ambas direcciones |

Centralizar la regla hace que asignaciones, argumentos, retornos, elementos de
arreglo, `case` de un `switch` y ramas de un ternario compartan una sola noción
de compatibilidad.

**`_element_fits(a, b)`** decide si un arreglo de `a` cabe donde se espera uno
de `b`. Es invariante para tipos reales: `integer[]` no entra en `float[]` aunque
un `integer` suelto sí entre en un `float`, porque el mismo arreglo quedaría
accesible bajo los dos nombres y se podría escribir un `float` en un
`integer[]`. Es permeable a `Unknown`/`Error` de forma recursiva, porque el
marcador puede estar varios niveles abajo (en `[[]]` el elemento externo es
`unknown[]`, no un `UnknownType` directo).

## 2. Tabla de símbolos y ámbitos (`symbols.py`)

**`Symbol`**: `name`, `kind`, `type`, `line`, `column`. `kind` (`VARIABLE`,
`CONSTANT`, `PARAMETER`, `FUNCTION`, `CLASS`) responde otra pregunta que `type`:
`let x: integer` y `const K: integer` tienen el mismo tipo y distinto kind, y esa
diferencia permite rechazar la reasignación de una constante. Los campos de
memoria (`size`, `offset`, `address`, `label`, `tac_name`) los completa
`layout.py` en el P2 (ver [`tac.md`](tac.md) §9).

**`Scope`**: un diccionario `nombre → Symbol`, un puntero `parent` y una lista
`children`. Las dos direcciones son distintas:

- **`parent` (hacia arriba)** es lo que recorre `resolve(name)`: este ámbito,
  luego el padre, hasta el global. Ese bucle *es* el alcance léxico, y es la
  razón de que los closures funcionen sin código especial: el ámbito de una
  función anidada encadena con el de su contenedora.
- **`children` (hacia abajo)** convierte los ámbitos en un **árbol permanente**.
  La pila de ámbitos abiertos (`SymbolTable`) es transitoria y se vacía al salir
  de cada bloque, función o clase, pero nada se destruye: `enter_scope` agrega el
  `Scope` a la pila y a `children` de su padre; `exit_scope` solo desapila. Del
  árbol que queda colgando de `global_scope` salen el panel de símbolos del IDE
  (`Scope.to_dict()`) y el layout de memoria del P2.

`resolve_local` (solo el ámbito actual) sirve para **redeclaración** (`let x` dos
veces en el mismo bloque es error, sombrear una `x` externa es legal) y para
**miembros de clase**, que no deben caer a un global homónimo.

Las cuatro operaciones que evalúa el proyecto:

| Operación | Cómo se implementa |
|---|---|
| **Insertar** | `Scope.declare(symbol)`: agrega al ámbito actual; `False` si el nombre ya existía *en ese mismo ámbito* |
| **Recuperar** | `Scope.resolve(nombre)`: busca en el ámbito actual y sube por `parent` |
| **Actualizar** | se reasigna el `type` de un `Symbol` ya declarado, en la primera asignación de una variable sin anotación (de `UnknownType` a su tipo real) |
| **Manejo de ámbitos** | `enter_scope`/`exit_scope`, siempre dentro de un `try/finally` para no dejar la pila desbalanceada si una regla reporta un error a media visita |

## 3. El checker (`checker.py`)

### 3.1 Visitor y convención de retorno

`SemanticChecker` hereda de `CompiscriptVisitor` (generado), que trae un método
por regla de la gramática, todos con `return self.visitChildren(ctx)`. Se hereda
un recorrido completo que no valida nada y solo se sobreescriben los métodos que
importan.

Se eligió **Visitor sobre Listener** porque cada `visitXxx` puede **devolver un
valor**: visitar una expresión devuelve su `Type`. Con Listener habría que
llevar una pila manual de resultados. `_visit_type(ctx)` es el helper usado en
los ~40 puntos donde se necesita ese tipo; convierte el `None` de un método no
sobreescrito en `ErrorType()`, para no llamar `.is_assignable_to` sobre `None`.

Consecuencias de sobreescribir un método:

- Uno se hace cargo de la recursión: si no llama `visitChildren` ni `self.visit`
  sobre los hijos, ese subárbol deja de visitarse en silencio.
- Cada hijo debe visitarse **exactamente una vez**: cero veces es una zona que
  nunca se valida, dos veces duplica los mensajes.

### 3.2 Atributos sintetizados y heredados

**Sintetizados (de abajo hacia arriba)**: el valor de retorno de cada `visitXxx`.
Las hojas fabrican un `Type` desde su texto o su símbolo; los operadores combinan
los tipos de sus operandos. `visitArrayLiteral` sintetiza un `ArrayType`
unificando los de sus elementos.

**Heredados (de arriba hacia abajo)**: contexto que un nodo necesita y no puede
calcular mirando a sus hijos. Como el proyecto usa Visitor, se implementa con
estado en `self`, empujado antes de recursar y sacado en un `finally`:

| Campo | Pregunta que responde | Empujado en | Leído en |
|---|---|---|---|
| `_function_return_stack` | ¿qué tipo debe devolver este `return`? ¿hay función alrededor? | `visitFunctionDeclaration` | `visitReturnStatement` |
| `_loop_depth` | ¿es legal un `break`/`continue` aquí? | los cuatro bucles | `visitBreakStatement`, `visitContinueStatement` |
| `_class_stack` | ¿a qué clase se refiere `this`? | `visitClassDeclaration` | `visitThisExpr` |
| `_chain_base` | ¿de qué tipo es lo que quedó a la izquierda en `a.b[c].d`? | cada eslabón de la cadena | el siguiente eslabón |
| `symbol.type` declarado | ¿qué tipo se espera de este inicializador? | `visitVariableDeclaration` | comparación con el tipo sintetizado |

`_loop_depth` es un **contador**, no un booleano: con un booleano, salir de un
bucle interno lo apagaría aunque el recorrido siga dentro de uno externo. El
patrón es siempre `+= 1` / `try: ... finally: -= 1` (igual con
`_class_stack` y `_function_return_stack`); el `finally` evita que un error a
media visita deje el estado corrupto para el resto del archivo.

### 3.3 Lo que hubo que resolver a mano por ANTLR

El visitor por defecto delega en `visitChildren`, que devuelve el resultado del
**último** hijo. Eso basta para sentencias, pero rompe la propagación de tipos:

- **`visitLiteralExpr`**: la gramática declara `Literal` antes que sus subtipos,
  y por el desempate de ANTLR todo literal numérico o de cadena lexea como el
  token genérico. El tipo se decide por el **texto**: empieza con `"` → `string`;
  contiene `.` → `float`; si no, `integer`.
- **`visitPrimaryExpr`**: debe manejar `'(' expression ')'` a mano; el último
  hijo sería el token `')'`.
- **`visitLeftHandSide`**: encadena el tipo base a través de cada `suffixOp`
  (`.miembro`, `[índice]`, llamada) con `_chain_base`.

Y una convención transversal en los operadores `sub (OP sub)*` (toda la cadena
`logicalOr → … → unary`): cuando `(OP sub)*` **no aparece**, el método debe ser
un **cable, no un chequeo**: devuelve el tipo del único operando. Toda expresión
atraviesa la cadena completa, así que forzar `BooleanType` ahí tiparía como
boolean a *toda* expresión.

### 3.4 Anotaciones para el generador de TAC (P2)

El checker también guarda, por `id(ctx)` de cada nodo: `node_types`,
`node_symbols`, `node_scopes` y `node_inner_scopes`. Sobrescribe `visit()` y
`visitChildren()` para que ningún nodo quede sin anotar. Ver [`tac.md`](tac.md) §10.

## 4. Reglas semánticas

**Ámbito y declaraciones.** `visitBlock` abre un `Scope` `BLOCK` por cada
`{ ... }`. `visitVariableDeclaration` declara en el ámbito actual (error si ya
existe ahí), usa la anotación o infiere del inicializador, y sin ninguna de las
dos queda en `UnknownType` hasta la primera asignación. `visitConstantDeclaration`
es análogo: la gramática obliga `= expression`, así que la inicialización
obligatoria sale de la sintaxis. `visitClassDeclaration` abre un `Scope` `CLASS`,
valida la clase base y apunta `ClassType.members` al **mismo** diccionario del
ámbito (no a una copia) para que `this.campo` resuelva mientras el cuerpo se
visita.

**Tipos y funciones.** Aritméticos: `integer`/`float` con promoción a `float`;
`+` también concatena `string + string`. Lógicos: `boolean`. Relacionales:
numéricos. Igualdad: tipos compatibles en cualquier dirección. Ternario:
condición `boolean`, ramas compatibles, resultado el tipo más general. Una
función no-`void` debe retornar en todos sus caminos (`_always_returns`, ver §9).
La asignación son dos métodos porque la gramática la parte: `x = 5;` es la
sentencia `assignment`, pero `arr[0] = 5;` cae en `expressionStatement →
assignmentExpr` (`visitAssignExpr`); ambos tratan igual el estrechamiento de
`UnknownType`. Las funciones se declaran en el ámbito **contenedor**, antes de
entrar al propio, para que la recursión resuelva su nombre; redeclarar es error
porque no hay sobrecarga.

**Condiciones.** `if`/`while`/`do-while`/`for` visitan la condición y reportan si
no es `BooleanType` ni `ErrorType`. `do-while` visita el cuerpo antes que la
condición, como se ejecuta. `for` abre su propio `Scope` para que
`for (let i = 0; ...)` no filtre `i`. `switch` no exige `boolean`: exige que cada
`case` sea comparable con la expresión, **en ambas direcciones**, para que
`switch (unEntero) { case unFloat: ... }` siga siendo válido por la promoción.

**`break`/`continue`** reportan si `_loop_depth == 0`; **`return` fuera de
función** si `_function_return_stack` está vacía.

**Código muerto.** `visitBlock` recorre sus sentencias con una bandera; tras un
`return`/`break`/`continue`, la primera sentencia siguiente **en ese bloque**
dispara un único error. La sentencia se sigue visitando para no perder otros
errores. No se propaga fuera del bloque (ver §9).

**Acceso `.`.** Lectura (`visitPropertyAccessExpr`) y escritura comparten la
resolución de miembros. La escritura se conecta a **dos** alternativas de la
gramática: `obj.campo = valor;` matchea `assignment`, mientras que `a.b.c = v;` o
una asignación dentro de otra expresión cae en `PropertyAssignExpr`. Ambas
delegan en `_check_property_assignment`, que valida en este orden: el objeto es
una clase → el miembro existe → no es constante → el tipo es compatible. Así el
orden de validaciones y los mensajes son idénticos sin importar la forma
sintáctica. `_resolve_member` sube por la cadena de herencia, y es lo que usa
`visitNewExpr` para encontrar el `constructor` heredado.

**`new`** resuelve la clase; sin `constructor` solo acepta `new C()`, con él
valida aridad y tipo de cada argumento. Devuelve siempre el `ClassType`, incluso
con argumentos inválidos, para no cascadear errores. **`this`** reporta si no hay
un `Scope` `CLASS` entre los ancestros; si lo hay, devuelve el tope de
`_class_stack`.

**Arreglos.** `visitArrayLiteral` acumula un tipo: si el siguiente elemento cabe
en el acumulado sigue igual; si el acumulado cabe en el siguiente, se ensancha
(`[1, 2.5]` da `float[]`); si ninguno cabe, error. `[]` sintetiza
`ArrayType(UnknownType())`. `visitIndexExpr` exige un `ArrayType` y un índice
`integer`; el tamaño no se valida porque no se conoce al compilar.

## 5. Recuperación de errores

El enunciado prohíbe detenerse en el primer error y exige evitar mensajes
repetidos o derivados. Por fase:

- **Léxico**: ANTLR sigue tokenizando tras un carácter no reconocido; el
  `ErrorListener` propio (`src/error_listener.py`) lo registra en español con
  línea y columna. Un error sintáctico causado por texto que el lexer descartó se
  omite, para no reportar dos veces el mismo problema.
- **Sintáctico**: recuperación en modo pánico nativa de ANTLR.
- **Semántico**: el checker nunca lanza una excepción ni interrumpe el recorrido;
  cada regla agrega un mensaje a `SemanticErrorList` y continúa. Toda
  subexpresión con un error ya reportado devuelve `ErrorType()`.

## 6. Integración con el IDE

`compiler.analyze()` devuelve `errors`, `status_message`, `tree_json`,
`symbol_table_json`, `tac` y `tac_stats`. `symbol_table_json` es `None` (no un
diccionario vacío) cuando el análisis semántico no llegó a correr, para que el
frontend distinga "no hay símbolos" de "no se llegó". `server.py` expone
`/api/run` y guarda `workspace/output/<nombre>/<nombre>.cps.{out,tree,symbols,tac}`.

El frontend (`frontend/`, React + Monaco) tiene: explorador de archivos (elige el
archivo de entrada), editor con resaltado propio, panel de salida con errores
navegables y botón **▶ Compilar**, visor del árbol de derivación y visor de la
tabla de símbolos (ámbitos anidados con sus símbolos, tipo y ubicación). El visor
de TAC y los datos de memoria en la tabla son del P2 ([`tac.md`](tac.md) §10).

## 7. Pruebas

La batería vive en `src/tests/semantic/<categoría>/` con la convención
`valido_<regla>.cps` / `invalido_<regla>.cps`, descubierta por glob desde
`test_<categoría>.py`: agregar un caso es agregar un `.cps`.
`src/tests/test_smoke.py` y `test_analyze.py` corren muestras por el pipeline
completo. `make test` ejecuta **466 pruebas** (P1 y P2 juntas).

| Carpeta | Casos | Regla del enunciado que cubre |
|---|---|---|
| `tipos/` | 11 | sistema de tipos: aritmética, lógicas, comparaciones, asignación inferida y anotada, `const`, reasignar constante |
| `ambito/` | 10 | resolución en bloques anidados, sombreado legal, no declarada, redeclaración, ámbito de `foreach` |
| `funciones/` | 9 | recursión, closures, argumentos, tipo de retorno, redeclaración (también dentro de un closure), retorno en todos los caminos |
| `control_flujo/` | 11 | condiciones no booleanas, `switch`/`case` compatibles e incompatibles, `break`/`continue` fuera de bucle, `return` fuera de función |
| `clases/` | 11 | atributos y métodos, herencia, miembro inexistente, constructor, `this`, escritura con `.` |
| `arreglos/` | 6 | tipos de elementos, índice no entero, indexar un no-arreglo, arreglo vacío, invariancia |
| `generales/` | 7 | código muerto tras `return`/`break`/`continue`, declaraciones duplicadas, expresiones sin sentido |

Dos puntos del enunciado no llevan caso inválido a propósito: la
**inicialización obligatoria de constantes** (la gramática no permite omitirla) y
la **creación de un ámbito por función, clase o bloque** (no es una condición de
error; se comprueba en la tabla de símbolos generada).

Lo que no cubre la batería: el endpoint HTTP y el frontend no tienen pruebas
automatizadas; se verificaron a mano.

## 8. Decisiones de diseño

| Decisión | Resolución |
|---|---|
| `float` no existía en la gramática heredada pero el enunciado lo exige | Se extendió antes de repartir el trabajo: `float` en `baseType` y `FloatLiteral` |
| Listener o Visitor | **Visitor**: cada `visit` devuelve el `Type` del nodo (§3.1) |
| `let x = 5;` sin anotación | El tipo se infiere del inicializador; sin inicializador queda `unknown` hasta la primera asignación |
| `null` | Asignable a arreglos y clases; nunca a primitivos |
| Sobrecarga de funciones | No soportada: redeclarar con el mismo nombre es error |
| Promoción numérica | `integer` → `float`, nunca al revés |
| `string + string` | Permitido (el propio lenguaje lo usa: `"Hola " + nombre`) |
| Arreglos | Invariantes para tipos reales (soundness ante aliasing) |
| `[]` vacío | Entra en cualquier arreglo, pero no estrecha el símbolo permanentemente |
| Índices de arreglo | Solo se valida el **tipo**; el tamaño no se conoce estáticamente |
| `try`/`catch` | En el P1 solo se recorría. Con el P2 se declara la variable del `catch` (tipo `string`, visible solo en el manejador) y un `try`/`catch` cuenta como retorno garantizado si ambos bloques retornan |
| `break`/`continue` | Solo dentro de bucles (restricción del enunciado); un `switch` no es destino de `break` |
| Idioma de los mensajes | Español, con línea y columna, igual en las tres fases |
| `let x = x + 1;` | La `x` de la derecha resuelve a la nueva declaración en vez de reportar "no declarada". Comportamiento conocido, no resuelto de forma definitiva |

## 9. Limitaciones conocidas

- **No hay hoisting.** Una función o clase usada antes de su declaración no
  resuelve, porque declarar es un efecto de visitar el nodo en orden. Se
  arreglaría con una pasada previa sobre las declaraciones de nivel superior.
- **`_resolve_type_node` no reporta clases no declaradas** (`let x: Foo;` con
  `Foo` inexistente pasa en silencio): consecuencia de no tener hoisting, ya que
  reportarlo daría falsos positivos sobre clases declaradas más abajo.
- **El código muerto no sale de un bloque anidado.** En `{ return 1; } print("x");`
  el `print` no se reporta, porque el bloque externo ve una sentencia `block`, no
  un `return`. Tampoco con un `if`/`else` cuyas dos ramas retornan.
- **El retorno garantizado es conservador.** `_always_returns` reconoce un
  `return`, un bloque que contiene uno, y un `if`/`else` o `try`/`catch` con
  ambas ramas retornando. Un bucle nunca cuenta, así que `while (true) { return 1; }`
  se reporta como "no garantiza retorno".
- **No se valida la sobreescritura de métodos** (firma compatible) en una subclase.
- **`ClassType.__eq__` compara solo por nombre**: dos clases homónimas en ámbitos
  distintos serían el mismo tipo.

Las limitaciones de la generación de código intermedio están en
[`tac.md`](tac.md) §11.

## 10. Autoría (Proyecto 1)

El trabajo se repartió por **categorías de reglas semánticas**, no por los
componentes de la ponderación (IDE / analizador / tabla de símbolos), porque
`checker.py` es un solo archivo y así se avanza en paralelo sin pisarse: cada
quien agrega sus propios `visitXxx`, y la única coordinación es sobre las
estructuras compartidas de `types.py` y `symbols.py`, acordadas en una fase
inicial conjunta (extender la gramática con `float` y definir las interfaces).
La referencia final es el historial de commits de cada integrante.

| Integrante (usuario de GitHub) | Área | Código principal |
|---|---|---|
| Camila Richter (`Cami`) | Tabla de símbolos y ámbito | `symbols.py`; en `checker.py`: `visitBlock`, `visitVariableDeclaration`, `visitIdentifierExpr`, `visitAssignment`, `visitClassDeclaration`, `visitForeachStatement`, `_resolve_type_node` |
| Marinés García (`NESHGP04`) | Sistema de tipos y funciones | `types.py`; en `checker.py`: literales y expresiones primarias, todos los operadores, `visitConstantDeclaration`, `visitAssignExpr`, `visitFunctionDeclaration`, `visitCallExpr`, `visitReturnStatement`, `_chain_base`, `_visit_type` |
| Jose Antonio Mérida (`TonitoMC`) | Control de flujo, clases, arreglos, IDE | en `checker.py`: `_loop_depth`, `_class_stack`, `_resolve_member`, condiciones de `if`/`while`/`do-while`/`for`/`switch`, `break`/`continue`, código muerto, `visitPropertyAccessExpr`, `_check_property_assignment`, `visitPropertyAssignExpr`, `visitNewExpr`, `visitThisExpr`, `visitIndexExpr`, `visitArrayLiteral`, `_element_fits`; integración con el IDE (endpoint y panel de tabla de símbolos) |
