# Arquitectura del análisis semántico — Compiscript

Documento consolidado de `src/semantic/`. Para el detalle método por
método de control de flujo, clases y arreglos ver
[ModuloControlFlujo.md](./ModuloControlFlujo.md).

La división de tareas y el estado del proyecto se llevan en el plan de
trabajo del equipo (`PlanCompis.md`, fuera del repositorio).

---

## 1. Panorama

El análisis semántico es una segunda pasada sobre el árbol que ya construyó
el parser. Responde las preguntas que una gramática libre de contexto no
puede hacer — "¿esta variable fue declarada?", "¿`"hola" - 3` es válido?",
"¿este `break` está dentro de un bucle?" — porque todas requieren
**recordar** algo a lo largo del programa, y una gramática no tiene
memoria.

```
código fuente
   │  CompiscriptLexer            caracteres → tokens
   ▼
tokens
   │  CompiscriptParser           tokens → árbol de análisis
   ▼
árbol
   │  SemanticChecker             árbol → errores + tabla de símbolos
   ▼
errores[]  +  árbol de ámbitos
```

`src/compiler.py` orquesta las tres etapas y es el único lugar que conoce
el pipeline completo; tanto el CLI (`main.py`) como el servidor
(`server.py`) pasan por ahí para no divergir.

**El análisis semántico solo corre si no hubo errores léxicos ni
sintácticos.** ANTLR se recupera de errores de sintaxis inventando y
saltando tokens, así que recorrer ese árbol produciría una avalancha de
errores semánticos falsos encima del error real.

### Archivos

| Archivo | Rol |
|---|---|
| `src/grammar/Compiscript.g4` | Gramática. Fuente de verdad de qué formas existen. |
| `src/generated/` | Lexer, parser y visitor generados por `make generate`. Nunca se editan a mano. |
| `src/semantic/types.py` | Jerarquía de tipos y reglas de asignabilidad. |
| `src/semantic/symbols.py` | `Symbol`, `Scope`, `SymbolTable`. |
| `src/semantic/errors.py` | `SemanticError` y su lista acumulada. |
| `src/semantic/checker.py` | `SemanticChecker`: el recorrido y todas las reglas. |
| `src/compiler.py` | Pipeline compartido. |
| `src/server.py` + `frontend/` | IDE: endpoint `/api/run` y paneles. |

## 2. Autoría

La división viene del plan de trabajo del equipo. Los commits
individuales son la referencia final; esto es el resumen.

| Persona | Área | Código principal |
|---|---|---|
| **Camila Richter** (Persona 1) | Tabla de símbolos y ámbito | `symbols.py` completo; en `checker.py`: `visitBlock`, `visitVariableDeclaration`, `visitIdentifierExpr`, `visitAssignment`, `visitClassDeclaration`, `visitForeachStatement`, `_resolve_type_node` |
| **NESHGP04** (Persona 2) | Sistema de tipos y funciones | Esqueleto de Fase 0 y `types.py`; en `checker.py`: literales y expresiones primarias, todos los operadores, `visitConstantDeclaration`, `visitAssignExpr`, `visitFunctionDeclaration`, `visitCallExpr`, `visitReturnStatement`, `_chain_base`, `_visit_type` |
| **TonitoMC** (Persona 3) | Control de flujo, clases, arreglos, IDE | En `checker.py`: `_loop_depth`, `_class_stack`, `_resolve_member`, condiciones de `if`/`while`/`do-while`/`for`/`switch`, `break`/`continue`, código muerto, `visitPropertyAccessExpr`, `_check_property_assignment`, `visitPropertyAssignExpr`, `visitNewExpr`, `visitThisExpr`, `visitIndexExpr`, `visitArrayLiteral`, `_element_fits`; integración con el IDE (endpoint + panel de tabla de símbolos) |

Fase 0 (extender la gramática con `float`, definir las interfaces de
`types.py`/`symbols.py`/`errors.py` y el esqueleto de `checker.py`) fue
trabajo conjunto previo al reparto.

## 3. Estructuras de datos

### 3.1 `types.py` — el vocabulario de tipos

Toda expresión del lenguaje evalúa a una de estas clases, y todo método
`visit` que maneje una expresión devuelve una:

- **Primitivos**: `BooleanType`, `IntegerType`, `FloatType`, `StringType`.
- **Compuestos**: `ArrayType(element)`, `FunctionType(params, ret)`,
  `ClassType(name, parent, members)`.
- **De maquinaria**: `VoidType` (función sin tipo de retorno),
  `NullType`, `UnknownType`, `ErrorType`.

`UnknownType` es "todavía no se sabe": lo producen `let x;` sin anotación
ni inicializador, un parámetro sin `: type`, y `[]`. Acepta cualquier cosa
y se fija con la primera asignación.

`ErrorType` es "ya se rompió y ya se reportó". Absorbe todo en ambas
direcciones para que un error real produzca **un** mensaje y no cinco.

**Toda la política del lenguaje vive en un método**,
`Type.is_assignable_to(target)` — "¿un valor de este tipo cabe donde se
espera `target`?". El caso base es igualdad exacta; las subclases lo
relajan:

| Tipo | Regla adicional |
|---|---|
| `IntegerType` | también cabe en `FloatType` (promoción, nunca al revés) |
| `NullType` | cabe en arreglos y clases, nunca en primitivos |
| `ClassType` | cabe en cualquier ancestro (`is_subclass_of`) |
| `ArrayType` | invariante para tipos reales; permeable a `Unknown`/`Error` (ver `_element_fits`, §5.3) |
| `Unknown` / `Error` | aceptan todo en ambas direcciones |

Centralizarlo es lo que hace que asignaciones, argumentos, retornos,
elementos de arreglo, `case` de un `switch` y ramas de un ternario
compartan una sola noción de compatibilidad.

`__eq__` compara por estructura y no por identidad — el checker crea
`IntegerType()` nuevo en cada punto, así que sin eso nada compararía igual
jamás. `__hash__` acompaña a `__eq__` por contrato de Python, y
`__repr__` devuelve `self.name` para que los mensajes de error digan
`integer[]` y no `<ArrayType object at 0x...>`.

### 3.2 `symbols.py` — la memoria

**`Symbol`**: `name`, `kind`, `type`, `line`, `column`. `kind`
(`VARIABLE`, `CONSTANT`, `PARAMETER`, `FUNCTION`, `CLASS`) responde una
pregunta distinta a `type`: `let x: integer` y `const K: integer` tienen
el mismo tipo y distinto kind, y esa diferencia es la que permite
rechazar la reasignación de una constante. `address` queda reservado, sin
usar, para las fases TAC/MIPS.

**`Scope`**: un diccionario `nombre → Symbol`, un puntero `parent` y una
lista `children`. Las dos direcciones importan y son distintas:

- **`parent` (hacia arriba)** es lo que recorre `resolve(name)`: este
  ámbito, luego el padre, hasta el global. Ese bucle *es* el alcance
  léxico, y es también la razón de que los closures funcionen sin código
  especial — el ámbito de una función anidada encadena con el de la
  función que la contiene.
- **`children` (hacia abajo)** convierte esto en un **árbol permanente**.
  La pila de `SymbolTable` es transitoria ("qué está abierto ahora") y se
  vacía al salir de cada construcción, pero nada se destruye: al terminar
  el recorrido, todo el árbol sigue colgando de `global_scope`. De ahí
  salen el panel del IDE (`to_dict()`) y los proyectos 2/3.

`resolve_local` (solo este ámbito) existe para dos casos: **redeclaración**
—`let x` dos veces en el mismo bloque es error, pero sombrear una `x`
externa es legal— y **miembros de clase**, que no deben caer a un global
homónimo.

**`SymbolTable`** es la pila de ámbitos abiertos: `enter_scope`,
`exit_scope`, `current`, y `declare`/`resolve` delegando al actual.

### 3.3 `errors.py`

`SemanticError(line, column, message)` con `__str__` en español, acumulado
en un `SemanticErrorList`. Misma forma que los errores léxicos/sintácticos
de `error_listener.py`, para que `compiler.py` solo tenga que concatenar
las dos listas.

## 4. El checker

### 4.1 Patrón visitor

`SemanticChecker` hereda de `CompiscriptVisitor` (generado), que trae un
método por regla de la gramática, todos con el mismo cuerpo por defecto:
`return self.visitChildren(ctx)`. Es decir, se hereda un recorrido
completo que no valida nada, y se sobreescriben solo los métodos que
interesan.

Se eligió Visitor sobre Listener porque cada `visitXxx` **devuelve un
valor**, y este proyecto usa esa vía como convención central: *visitar una
expresión devuelve su `Type`*. Con Listener habría que llevar una pila
manual de resultados.

Tres consecuencias prácticas:

- Lo que no se sobreescribe se recorre igual, gratis.
- **En el momento en que se sobreescribe un método, uno se hace cargo de
  la recursión.** Si el método no llama `visitChildren` ni `self.visit`,
  todo el subárbol deja de visitarse en silencio.
- Cada hijo debe visitarse **exactamente una vez**: cero veces es una zona
  muerta, dos veces son mensajes duplicados.

### 4.2 Las dos vías de información

- **Hacia arriba, por el valor de retorno**: los tipos. Las hojas
  (literales, identificadores) fabrican tipos; los operadores los combinan
  y validan; las sentencias los consumen.
- **Lateral, por estado en `self`**: lo que no está en el subárbol.

| Campo | Pregunta que responde |
|---|---|
| `symbols` | ¿qué nombres son visibles aquí? |
| `errors` | acumulador de errores |
| `_function_return_stack` | ¿qué tipo debe devolver `return`? ¿estoy en una función? |
| `_loop_depth` | ¿es legal `break`/`continue` aquí? |
| `_class_stack` | ¿a qué se refiere `this`? |
| `_chain_base` | ¿de qué tipo es lo que quedó a mi izquierda en la cadena? |

Son **pilas y contadores, no valores sueltos**, porque estas
construcciones se anidan. `_loop_depth` es un contador y no un booleano
justamente por eso: con un booleano, salir de un bucle interno lo pondría
en `False` aunque el recorrido siga dentro del externo, y un `break`
legítimo posterior se reportaría como error.

**Todo lo que se empuja se saca en un `finally`:**

```python
self.symbols.enter_scope(ScopeKind.BLOCK)
try:
    ...
finally:
    self.symbols.exit_scope()
```

Sin eso, un error a media visita dejaría el estado corrupto para *el resto
del archivo*.

### 4.3 Helpers compartidos

- **`_error(ctx, mensaje)`**: agrega un error anclado en `ctx.start`.
- **`_resolve_type_node(type_ctx)`**: traduce un nodo `type`
  (`baseType ('[' ']')*`) a un `Type`. Los primitivos salen de
  `PRIMITIVE_TYPES`; cualquier otro nombre es una clase, y se **reutiliza
  el `ClassType` ya declarado** (ver §5.3). Cada par `[]` envuelve el
  resultado en un `ArrayType`, así que `integer[][]` sale natural. Lo usan
  anotaciones, parámetros y tipos de retorno.
- **`_visit_type(ctx)`**: `self.visit(ctx)` convirtiendo `None` en
  `ErrorType()`. Existe porque un método no sobreescrito cae en el
  `visitChildren` por defecto y devuelve `None`, que no tiene
  `.is_assignable_to` y tumbaría el análisis.
- **`_is_numeric(t)`**, **`_operator_before(ctx, i)`**: utilidades. El
  segundo saca el texto del operador de una regla `sub (OP sub)*`; los
  operadores son tokens anónimos sin accesor generado, así que hay que
  indexar los hijos crudos (`2*i - 1`).
- **`_resolve_member(class_type, name)`**: busca un miembro subiendo por
  la cadena de herencia.

## 5. Las reglas

### 5.1 Ámbito y declaraciones

**`visitBlock`** abre un `Scope` de tipo `BLOCK` por cada `{ ... }`, así
que lo declarado adentro deja de existir al cerrar la llave.

**`visitVariableDeclaration`** declara el símbolo en el ámbito actual
(error si el nombre ya existe *en ese mismo ámbito*; sombrear uno externo
es legal). Con anotación, usa `_resolve_type_node` y verifica que el valor
inicial quepa; sin anotación, infiere del inicializador, y si tampoco hay
inicializador queda en `UnknownType` hasta la primera asignación.

**`visitIdentifierExpr`** es el lado de lectura: `resolve` por la cadena
de ámbitos, error si no existe, y devuelve `ErrorType()` para no
cascadear.

**`visitConstantDeclaration`** es igual pero para `CONSTANT` y sin rama de
`UnknownType`: la gramática ya obliga el `= expression`, así que
"inicialización obligatoria" sale gratis, y el tipo de una constante queda
fijo.

**`visitClassDeclaration`** registra la clase y abre un `Scope` de tipo
`CLASS` para sus miembros — eso es lo que evita que los atributos choquen
con variables del ámbito contenedor. Si hereda, valida que la clase base
exista y arma `ClassType.parent`. Apunta `class_type.members` al **mismo**
diccionario del ámbito (no una copia), para que `this.campo` resuelva
mientras el cuerpo todavía se está visitando.

### 5.2 Sistema de tipos y funciones

**Infraestructura de expresiones.** `visitLiteralExpr`, `visitPrimaryExpr`
y `visitLeftHandSide` no estaban en el reparto original pero sin ellas
ningún tipo se propaga:

- `visitLiteralExpr` determina el tipo mirando el **texto** del literal.
  La gramática declara `Literal: IntegerLiteral | FloatLiteral | StringLiteral;`
  *antes* que las tres específicas y todas hacen match del mismo texto;
  por el desempate de ANTLR (gana la declarada primero), todo literal
  lexea como el token genérico `Literal`. Empieza con `"` → `string`;
  contiene `.` → `float`; si no, `integer`.
- `visitPrimaryExpr` maneja `'(' expression ')'` a mano: el
  `visitChildren` por defecto devolvería el resultado del último hijo, o
  sea el token `')'`.
- `visitLeftHandSide` encadena el tipo base a través de los `suffixOp` vía
  `_chain_base`.

**Operadores.** Aritméticos: ambos operandos `integer` o `float`, con
promoción a `float` si alguno lo es; `+` además concatena
`string + string` (el propio `DefinicionCompiscript.md` usa
`"Hola " + nombre`). Lógicos: `boolean`. Relacionales: numéricos.
Igualdad: tipos compatibles en cualquier dirección. Ternario: condición
`boolean` y ramas compatibles, con el tipo más general como resultado.

**Regla clave de los operadores:** cuando la parte opcional `(OP sub)*` no
aparece, el método es un **cable, no un chequeo** — debe devolver el tipo
real del único operando. Como toda expresión atraviesa la cadena de
precedencia (`logicalOr → logicalAnd → equality → ...`), forzar
`BooleanType` ahí haría que *toda* expresión del lenguaje tipara como
boolean.

**Una constante no puede reasignarse.** El `Symbol` ya lleva el `kind`, así
que ambos caminos de asignación rechazan un `SymbolKind.CONSTANT` antes de
comparar tipos. La rúbrica solo pide inicialización obligatoria (que la
gramática garantiza), pero la inmutabilidad es lo que significa `const`.

**Una función no-`void` debe retornar en todos sus caminos**
(`_always_returns`, ver limitaciones en §9).

**Asignación está implementada en dos métodos**, porque la gramática la
parte en dos: `x = 5;` matchea la regla de sentencia `assignment`, pero
`arr[0] = 5;` no matchea ninguna de sus dos alternativas y cae en
`expressionStatement → assignmentExpr`, o sea `visitAssignExpr`. Ambos
deben tratar igual el narrowing de `UnknownType`.

**Funciones.** Se construye un `FunctionType(params, ret)` y se declara el
símbolo en el ámbito **contenedor**, *antes* de entrar al ámbito propio —
así la recursión resuelve su propio nombre y la función es llamable desde
afuera. Redeclarar es error (no hay sobrecarga). Un parámetro sin
anotación recibe `UnknownType` y acepta cualquier argumento.
`visitCallExpr` valida aridad y tipo posicional; `visitReturnStatement`
valida contra el tope de `_function_return_stack`. Recursión y closures
salieron gratis de la cadena de ámbitos.

### 5.3 Control de flujo, clases y arreglos

**Condiciones `boolean`** en `if`, `while`, `do-while`, `for` y `switch`.
Todas con la misma forma: visitar la expresión y reportar si no es
`BooleanType` ni `ErrorType` (se excluye `ErrorType` para no encadenar).
Detalles:

- `do-while` visita el cuerpo antes que la condición, siguiendo el orden
  real de ejecución.
- `for` abre su propio `Scope` de tipo `BLOCK` para que un
  `for (var i = 0; ...)` no filtre `i`. Sus dos expresiones son opcionales
  por separado, pero la gramática las emite en orden, así que la primera
  siempre es la condición.
- `switch` valida además que el tipo de cada `case` sea compatible con el
  de la expresión, en cualquier dirección.

**`break` / `continue`** reportan si `_loop_depth == 0`.

**`return` fuera de función**: primera condición de `visitReturnStatement`
— si `_function_return_stack` está vacía, no hay función alrededor.

**Código muerto**: `visitBlock` recorre sus statements con una bandera; al
pasar un `return`/`break`/`continue`, lo que siga **en ese mismo bloque**
es inalcanzable. Se reporta solo el primero, para que una región muerta dé
un error y no uno por línea.

**Acceso `.`** — lectura (`visitPropertyAccessExpr`) y escritura
(`_check_property_assignment`). La escritura está conectada a las **dos**
formas que permite la gramática: la sentencia `obj.campo = valor;`
(`visitAssignment`) y la alternativa etiquetada `visitPropertyAssignExpr`,
que aplica cuando la asignación está dentro de una expresión mayor o el
lado izquierdo tiene sufijos (`a.b.c = ...`). Valida, en orden: que el
objetivo sea un objeto, que el miembro exista (vía `_resolve_member`, así
que los heredados valen), que no sea constante, y que el valor quepa.

**Anotaciones de clase reutilizan el `ClassType` declarado.**
`_resolve_type_node` busca el símbolo en la tabla en vez de construir un
`ClassType` nuevo. Construir uno nuevo era un error real: como
`ClassType.__eq__` compara solo por nombre, el objeto nuevo comparaba
igual al verdadero y las asignaciones pasaban, pero llevaba `members`
vacío y `parent` en `None`, así que **toda variable declarada con
anotación de clase fallaba en cualquier acceso `.`**. Si el nombre no está
declarado (no hay hoisting), se mantiene el comportamiento permisivo en
vez de reportar un falso "no declarada".

**`new`** valida que el símbolo exista y sea de kind `CLASS`, luego busca
un miembro `constructor`: sin constructor solo se acepta `new C()` sin
argumentos; con constructor, valida aridad y tipos. Devuelve siempre el
`ClassType`, aun con argumentos malos, para no cascadear.

**`this`** reporta si no hay un `Scope` de kind `CLASS` entre los
ancestros; si lo hay, devuelve el tope de `_class_stack`.

**Arreglos.** `visitArrayLiteral` unifica los tipos de los elementos: si
el siguiente cabe en el acumulado sigue, si el acumulado cabe en el
siguiente ensancha (`[1, 2.5]` → `float[]`), y si ninguno cabe reporta.
Un `[]` vacío devuelve `ArrayType(UnknownType())`. `visitIndexExpr` valida
que el objetivo sea un arreglo y el índice `integer`.

**`_element_fits(a, b)`** (en `types.py`) decide si un arreglo de `a` cabe
donde se espera uno de `b`:

- **Invariante para tipos reales**: `integer[]` no entra en `float[]`
  aunque un `integer` suelto sí entre en un `float`. Si entrara, el mismo
  arreglo quedaría bajo los dos nombres y se le podría escribir un `float`
  a un `integer[]`.
- **Permeable a `Unknown`/`Error` a cualquier profundidad**: son
  marcadores, no tipos. Es lo que hace que `[]` entre en cualquier
  arreglo, incluso anidado (`[[]]` en un `integer[][]`). La recursión es
  necesaria porque el marcador puede estar varios niveles abajo: en `[[]]`
  el elemento externo es `unknown[]`, que no es un `UnknownType`.

## 6. Decisiones de diseño

| Decisión | Resolución |
|---|---|
| `float` no existía en la gramática oficial pero la rúbrica lo pide | Se extendió la gramática (Fase 0): `float` en `baseType` + `FloatLiteral` |
| Listener vs Visitor | **Visitor** — cada `visit` devuelve el `Type` del nodo |
| `let x = 5;` sin anotación | El tipo se infiere del inicializador; sin inicializador queda `unknown` hasta la primera asignación |
| `null` | Asignable a arreglos y clases; nunca a primitivos |
| Sobrecarga de funciones | **No soportada** — redeclarar es error |
| Promoción numérica | `integer` → `float`, nunca al revés |
| `string + string` | Permitido, aunque la rúbrica solo menciona `integer`/`float` para aritmética: el propio spec del lenguaje usa `"Hola " + nombre` |
| Arreglos | **Invariantes**: `integer[]` no entra en `float[]` (soundness ante aliasing) |
| `[]` vacío | Entra en cualquier arreglo, pero **no** estrecha el símbolo: tras `var a = []; a = [1,2];` el tipo de `a` sigue siendo `unknown[]` |
| Índices de arreglo | Solo se valida el **tipo** del índice; el tamaño no se conoce estáticamente |
| `new` con argumentos malos | Devuelve igual el `ClassType`, para no cascadear |
| `try`/`catch` | **Fuera de alcance** por decisión de equipo; el método existe como passthrough explícito |
| Idioma de los mensajes | Español, mismo estilo que `error_listener.py` |
| Declarar antes de visitar el inicializador | `let x = x + 1;` resuelve la `x` derecha a la nueva declaración en vez de reportar "no declarada" |

## 7. Integración con el IDE

`compiler.analyze()` devuelve `errors`, `status_message`, `tree_json` y
`symbol_table_json`. El último es `None` —no un diccionario vacío— cuando
el análisis semántico no llegó a correr, para que el frontend distinga
"no hay símbolos" de "no se llegó hasta ahí".

`server.py` lo expone en `/api/run` como `symbolTable`; `App.tsx` lo
consume y abre una pestaña de símbolos que renderiza
`SymbolTableViewer`, recorriendo el árbol de ámbitos producido por
`Scope.to_dict()`.

## 8. Tests

Una carpeta por categoría en `src/tests/semantic/`, con la convención
`valido_<regla>.cps` / `invalido_<regla>.cps` y un `test_<categoria>.py`
que los descubre por glob. Agregar un caso es agregar un `.cps`.

| Carpeta | Casos | Cubre |
|---|---|---|
| `ambito/` | 10 | resolución por bloques anidados, shadowing, no declarada, redeclaración, herencia, ámbito de `foreach` |
| `tipos/` | 11 | aritmética, lógicas, comparaciones, ternario, asignación inferida y anotada, `const`, reasignar constante |
| `funciones/` | 8 | recursión, closures, argumentos, tipo de retorno, redeclaración, invocar algo que no es función, retorno en todos los caminos |
| `control_flujo/` | 8 | condiciones no booleanas, `break`/`continue` fuera de bucle, `return` fuera de función |
| `clases/` | 8 | atributos y métodos, herencia, miembro inexistente, constructor, `this`, acceso por anotación, escritura `.` |
| `arreglos/` | 6 | tipos de elementos, índice no entero, indexar no-arreglo, arreglo vacío (incluido anidado), invariancia |
| `generales/` | 5 | código muerto, declaraciones duplicadas, expresiones sin sentido |

```
make test
```

## 9. Limitaciones conocidas

- **No hay hoisting.** Una función o clase usada antes de su declaración no
  resuelve, porque declarar es un efecto de visitar. Se arreglaría con una
  pasada previa que registre las declaraciones de nivel superior antes de
  revisar los cuerpos.
- **`_resolve_type_node` no reporta clases no declaradas** (`let x: Foo;`
  pasa en silencio), justamente por lo anterior: sin hoisting daría falsos
  positivos.
- **El código muerto no se propaga fuera de un bloque anidado.** En
  `{ return 1; } print("x");` el `print` es inalcanzable pero no se
  reporta, porque el bloque externo ve un statement de tipo `block`, no un
  `return`. Igual con un `if` cuyas dos ramas retornan. Detectarlo
  requiere análisis de alcanzabilidad recursivo.
- **El análisis de retorno es conservador.** `_always_returns` solo
  reconoce las formas que la gramática garantiza estáticamente: un
  `return`, un bloque que contiene uno, y un `if`/`else` donde ambas ramas
  retornan. Un bucle nunca cuenta, porque su cuerpo puede ejecutarse cero
  veces — así que `while (true) { return 1; }` se reporta aunque en la
  práctica siempre retorne. Reconocerlo requeriría evaluar la condición en
  tiempo de compilación.
- **No se valida la sobreescritura de métodos** en una subclase.
- **`ClassType.__eq__` compara solo por nombre**, así que dos clases
  homónimas en ámbitos distintos serían el mismo tipo.
