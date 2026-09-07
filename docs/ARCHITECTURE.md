# Arquitectura — Analizador Semántico de Compiscript

Documento único de arquitectura para el Proyecto 1 (Análisis Semántico) de
Compiladores 2 (CC3032). Consolida la división de trabajo, el diseño interno
de `src/semantic/` y el estado de la batería de pruebas frente al
enunciado (`docs/SemanticAnalysis.md`).

---

## 1. Panorama general

El compilador se construye por fases acumulativas (Aho et al., 2006):
léxico → sintáctico → semántico → (futuro: código intermedio y MIPS). Este
proyecto parte del analizador léxico/sintáctico de un laboratorio previo
del curso, hecho con ANTLR4, y le agrega el análisis semántico completo:
sistema de tipos, tabla de símbolos y validación de todas las reglas del
enunciado, integrado en un IDE web.

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
(`server.py`) pasan por ahí para no divergir. **El análisis semántico solo
corre si no hubo errores léxicos ni sintácticos**: ANTLR se recupera de
errores de sintaxis inventando y saltando tokens, así que recorrer ese
árbol dañado produciría una avalancha de errores semánticos falsos encima
del error real.

La única modificación hecha a la gramática heredada fue agregar el tipo
`float` (no estaba en la gramática oficial del laboratorio, pero el
enunciado exige verificar tipos entre `integer` y `float`): se añadió un
literal decimal (`FloatLiteral`) y `float` como alternativa de `baseType`,
y se regeneró el analizador con ANTLR sin tocar las reglas léxicas o
sintácticas existentes.

### Archivos

| Archivo | Rol |
|---|---|
| `src/grammar/Compiscript.g4` | Gramática. Fuente de verdad de qué formas existen. |
| `src/generated/` | Lexer, parser y visitor generados por `make generate`. Nunca se editan a mano. |
| `src/semantic/types.py` | Jerarquía de tipos y reglas de asignabilidad. |
| `src/semantic/symbols.py` | `Symbol`, `Scope`, `SymbolTable`. |
| `src/semantic/errors.py` | `SemanticError` y su lista acumulada. |
| `src/semantic/checker.py` | `SemanticChecker`: el recorrido y todas las reglas. |
| `src/compiler.py` | Pipeline compartido (léxico + sintáctico + semántico). |
| `src/server.py` + `frontend/` | IDE: endpoint `/api/run` y paneles de errores, árbol y tabla de símbolos. |

### Herramientas

- **ANTLR4 4.13.2**: genera lexer, parser y las clases base
  Listener/Visitor desde `src/grammar/Compiscript.g4`. Se usó el patrón
  **Visitor** para el recorrido semántico (ver §4.1).
- **Python 3.9** + `antlr4-python3-runtime` para el analizador semántico.
- **FastAPI + Uvicorn** para exponer el analizador como servicio HTTP
  local.
- **React + TypeScript + Vite + Monaco Editor** (el motor de VS Code)
  para el IDE web.
- **pytest** para la batería de pruebas automatizadas (`make test`).

## 2. División de trabajo

El trabajo se repartió por **categorías de reglas semánticas**, no por los
componentes de la ponderación (IDE / analizador / tabla de símbolos),
porque `checker.py` es un solo archivo y esa división permite avanzar en
paralelo sin pisarse. Una fase inicial conjunta (extender la gramática con
`float`, definir las interfaces de `types.py` / `symbols.py` / `errors.py`
y el esqueleto de `checker.py`) fue trabajo compartido antes del reparto.
La referencia final de quién hizo qué son los commits individuales; esto
es el resumen:

| Integrante (usuario de GitHub) | Área | Código principal |
|---|---|---|
| Camila Richter (`Cami`) | Tabla de símbolos y ámbito | `symbols.py` completo; en `checker.py`: `visitBlock`, `visitVariableDeclaration`, `visitIdentifierExpr`, `visitAssignment`, `visitClassDeclaration`, `visitForeachStatement`, `_resolve_type_node` |
| Marinés García (`NESHGP04`) | Sistema de tipos y funciones | `types.py`; en `checker.py`: literales y expresiones primarias, todos los operadores, `visitConstantDeclaration`, `visitAssignExpr`, `visitFunctionDeclaration`, `visitCallExpr`, `visitReturnStatement`, `_chain_base`, `_visit_type` |
| Jose Antonio Mérida (`TonitoMC`) | Control de flujo, clases, arreglos, IDE | En `checker.py`: `_loop_depth`, `_class_stack`, `_resolve_member`, condiciones de `if`/`while`/`do-while`/`for`/`switch`, `break`/`continue`, código muerto, `visitPropertyAccessExpr`, `_check_property_assignment`, `visitPropertyAssignExpr`, `visitNewExpr`, `visitThisExpr`, `visitIndexExpr`, `visitArrayLiteral`, `_element_fits`; integración con el IDE (endpoint + panel de tabla de símbolos) |

Esta separación en capas deja `checker.py` como el único punto real de
integración entre las tres áreas: cada quien agrega sus propios métodos
`visitXxx`, y la única coordinación necesaria es sobre las estructuras
compartidas de `types.py` y `symbols.py`, acordadas en la fase conjunta.

## 3. Sistema de tipos (`types.py`)

Toda expresión del lenguaje evalúa a una instancia de `Type`, y todo
método `visit` que maneje una expresión devuelve una (ver §5 sobre esta
convención):

- **Primitivos**: `BooleanType`, `IntegerType`, `FloatType`, `StringType`.
- **Compuestos**: `ArrayType(element)`, `FunctionType(params, ret)`,
  `ClassType(name, parent, members)`.
- **De maquinaria**, sin equivalente en el lenguaje fuente:
  - **`UnknownType`**: "todavía no se sabe". Lo producen `let x;` sin
    anotación ni inicializador, un parámetro sin `: type`, y `[]`. Acepta
    cualquier valor y se fija (narrowing) con la primera asignación —de
    forma permanente, el símbolo actualiza su `type` real.
  - **`ErrorType`**: "ya se rompió y ya se reportó". Se devuelve en lugar
    del tipo real tras reportar un error, y es compatible con cualquier
    tipo en ambas direcciones, para que una subexpresión ya inválida no
    dispare una cascada de errores derivados sobre cada nodo que la
    contiene.
  - **`VoidType`**: tipo de retorno de una función sin anotación, y
    **`NullType`**.

Toda la política del lenguaje vive en un solo método,
`Type.is_assignable_to(target)` — "¿un valor de este tipo cabe donde se
espera `target`?". El caso base es igualdad estructural (`__eq__` compara
por estructura, no por identidad, porque el checker crea instancias nuevas
en cada punto); las subclases lo relajan:

| Tipo | Regla adicional |
|---|---|
| `IntegerType` | también cabe en `FloatType` (promoción, nunca al revés) |
| `NullType` | cabe en arreglos y clases, nunca en primitivos |
| `ClassType` | cabe en cualquier ancestro (`is_subclass_of`, herencia) |
| `ArrayType` | invariante para tipos reales; permeable a `Unknown`/`Error` a cualquier profundidad (`_element_fits`) |
| `Unknown` / `Error` | aceptan todo en ambas direcciones |

Centralizar esta regla es lo que hace que asignaciones, argumentos,
retornos, elementos de arreglo, `case` de un `switch` y ramas de un
ternario compartan una sola noción de compatibilidad, en vez de reimplementar
la comparación en cada regla semántica.

**`_element_fits(a, b)`** decide si un arreglo de `a` cabe donde se espera
uno de `b`. Es invariante para tipos reales (`integer[]` no entra en
`float[]` aunque un `integer` suelto sí entre en un `float`: si entrara, el
mismo arreglo quedaría accesible bajo los dos nombres y se le podría
escribir un `float` a un `integer[]`, rompiendo *soundness* ante
aliasing) pero permeable a `Unknown`/`Error` a cualquier profundidad
(recursivo, porque el marcador puede estar varios niveles abajo: en
`[[]]` el elemento externo es `unknown[]`, que no es un `UnknownType`
directo).

## 4. Tabla de símbolos y ámbitos (`symbols.py`)

**`Symbol`**: `name`, `kind`, `type`, `line`, `column`. `kind` (`VARIABLE`,
`CONSTANT`, `PARAMETER`, `FUNCTION`, `CLASS`) responde una pregunta
distinta a `type`: `let x: integer` y `const K: integer` tienen el mismo
tipo y distinto kind, y esa diferencia es la que permite rechazar la
reasignación de una constante. `address` queda reservado, sin usar, para
las fases de TAC/MIPS.

**`Scope`**: un diccionario `nombre → Symbol`, un puntero `parent` y una
lista `children`. Las dos direcciones importan y son distintas:

- **`parent` (hacia arriba)** es lo que recorre `resolve(name)`: busca en
  este ámbito, luego en el padre, hasta el global. Ese bucle *es* el
  alcance léxico, y es también la razón de que los closures funcionen sin
  código especial — el ámbito de una función anidada encadena con el de la
  función que la contiene, así que resolver una variable capturada es
  exactamente el mismo camino que resolver cualquier otra.
- **`children` (hacia abajo)** convierte esto en un **árbol permanente**,
  no en una simple pila. La pila de ámbitos abiertos (`SymbolTable`) es
  transitoria — "qué está abierto ahora mismo mientras se visita el
  árbol" — y se vacía al salir de cada bloque/función/clase, pero nada se
  destruye: `enter_scope` agrega el nuevo `Scope` tanto a la pila
  (transitoria) como a `children` del scope padre (permanente); `exit_scope`
  solo desapila. Al terminar el recorrido completo, el árbol entero sigue
  colgando de `global_scope`, aunque la pila ya esté vacía. De ese árbol
  salen el panel de símbolos del IDE (`Scope.to_dict()`) y lo que
  reutilizarán las fases de TAC y MIPS.

`resolve_local` (busca solo en el ámbito actual, sin subir) existe para dos
casos: **redeclaración** (`let x` dos veces en el mismo bloque es error,
pero sombrear una `x` externa en un bloque anidado es legal — por eso
`declare()` solo revisa `self.symbols`, nunca los ancestros) y **miembros
de clase**, que no deben caer a un global homónimo.

**`SymbolTable`** es la pila de ámbitos abiertos: `enter_scope`,
`exit_scope`, `current`, y `declare`/`resolve` que delegan al ámbito
actual. Las cuatro operaciones que evalúa el proyecto quedan así:

| Operación | Cómo se implementa |
|---|---|
| **Insertar** | `Scope.declare(symbol)`: agrega al scope actual, devuelve `False` si el nombre ya existía *en ese mismo scope* (no en los ancestros) |
| **Recuperar** | `Scope.resolve(nombre)`: busca en el scope actual y sube por `parent` hasta el global |
| **Actualizar** | se reasigna el campo `type` de un `Symbol` ya declarado, en la primera asignación de una variable sin anotación (narrowing de `UnknownType` a su tipo real) |
| **Manejo de ámbitos** | `enter_scope`/`exit_scope`, siempre dentro de un `try/finally` para no dejar la pila desbalanceada si una regla reporta un error a media visita |

## 5. El checker (`checker.py`)

### 5.1 Patrón visitor y la convención de retorno

`SemanticChecker` hereda de `CompiscriptVisitor` (generado), que trae un
método por regla de la gramática, todos con el mismo cuerpo por defecto:
`return self.visitChildren(ctx)`. O sea que se hereda gratis un recorrido
completo que no valida nada, y solo se sobreescriben los métodos que
importan.

Se eligió **Visitor sobre Listener** porque cada `visitXxx` puede
**devolver un valor**, y el proyecto entero usa esa vía como convención
central: **visitar una expresión devuelve su `Type`**. Con Listener habría
que llevar una pila manual de resultados a mano. `_visit_type(ctx)` es el
helper usado en los ~40 puntos donde se necesita ese tipo: llama
`self.visit(ctx)` y convierte un `None` (lo que devuelve un método no
sobreescrito, porque `visitChildren` por defecto no propaga nada útil) en
`ErrorType()`, para que nunca se intente llamar `.is_assignable_to` sobre
`None`.

Tres consecuencias prácticas de este diseño:

- Lo que no se sobreescribe se recorre igual, gratis.
- **En el momento en que se sobreescribe un método, uno se hace cargo de
  la recursión.** Si el método no llama `visitChildren` ni `self.visit`
  sobre sus hijos, todo ese subárbol deja de visitarse en silencio.
- Cada hijo debe visitarse **exactamente una vez**: cero veces es una
  zona muerta que nunca se valida, dos veces produce mensajes de error
  duplicados.

### 5.2 Atributos sintetizados vs. heredados

En términos clásicos de gramáticas de atributos, el checker usa **ambas**
direcciones de flujo de información sobre el mismo árbol:

**Sintetizados (de abajo hacia arriba)**: el valor de retorno de cada
`visitXxx`. Las hojas (literales, identificadores) fabrican un `Type` a
partir de su propio texto o símbolo; los operadores combinan los tipos
sintetizados de sus operandos y sintetizan uno nuevo; las sentencias
consumen el tipo sintetizado de sus subexpresiones. Ejemplo:
`visitArrayLiteral` sintetiza un `ArrayType` unificando los tipos ya
sintetizados de cada elemento.

**Heredados (de arriba hacia abajo)**: información que un nodo necesita
del contexto en el que aparece, y que no puede calcularse solo mirando a
sus hijos. Como el proyecto usa Visitor (no una gramática de atributos
declarativa), esto se implementa con **estado en `self`**, empujado antes
de recursar y sacado en un `finally` al terminar — son pilas y contadores,
no valores sueltos, porque las construcciones que representan se anidan:

| Campo | Pregunta que responde | Empujado en | Leído en |
|---|---|---|---|
| `_function_return_stack` | ¿qué tipo debe devolver este `return`? ¿hay una función alrededor? | `visitFunctionDeclaration`, con el tipo de retorno declarado | `visitReturnStatement` |
| `_loop_depth` | ¿es legal un `break`/`continue` aquí? | `visitWhileStatement`, `visitDoWhileStatement`, `visitForStatement`, `visitForeachStatement` | `visitBreakStatement`, `visitContinueStatement` |
| `_class_stack` | ¿a qué clase se refiere `this`? | `visitClassDeclaration`, con el `ClassType` de la clase que se está definiendo | `visitThisExpr` |
| `_chain_base` | ¿de qué tipo es lo que quedó a la izquierda en esta cadena `a.b[c].d`? | cada eslabón de `visitLeftHandSide`/`visitPropertyAccessExpr`, con el tipo ya sintetizado del eslabón anterior | el siguiente eslabón (`visitPropertyAccessExpr`, `visitIndexExpr`) |
| `symbol.type` (declarado) | ¿qué tipo se espera para este inicializador? | `visitVariableDeclaration`, al leer la anotación | se compara contra el tipo sintetizado del inicializador antes de aceptarlo o de inferir |

`_loop_depth` es deliberadamente un **contador**, no un booleano: con un
booleano, salir de un bucle interno lo pondría en `False` aunque el
recorrido siga dentro de un bucle externo, y un `break` legítimo
inmediatamente después se reportaría como error. Como contador,
incrementar/decrementar en cada nivel anidado preserva la profundidad real
sin importar cuántos bucles se hayan cerrado ya.

El patrón general para empujar/sacar este estado heredado es siempre:

```python
self._loop_depth += 1
try:
    ...  # visitar el cuerpo del bucle
finally:
    self._loop_depth -= 1
```

(mismo patrón para `_class_stack.append/pop` alrededor del cuerpo de una
clase, y `_function_return_stack.append/pop` alrededor del cuerpo de una
función.) El `finally` es lo que evita que un error a media visita deje el
estado corrupto para el resto del archivo — sin él, un `return` con tipo
incorrecto en la mitad de una función podría dejar la pila de retorno
desbalanceada y afectar la validación de todo lo que viene después.

### 5.3 Recorrido de ANTLR: qué hubo que resolver a mano

ANTLR genera un método `visitXxx` por cada alternativa etiquetada de la
gramática, y el visitor por defecto de una regla sin acciones simplemente
delega en `visitChildren`, que a su vez devuelve el resultado de **el
último hijo visitado**. Eso alcanza para sentencias (no importa el
retorno), pero rompe la propagación de tipos en varios puntos que no son
"reglas" en sí mismas pero son indispensables para que el resto funcione:

- **`visitLiteralExpr`**: la gramática declara
  `Literal: IntegerLiteral | FloatLiteral | StringLiteral;` antes que las
  alternativas específicas, y las tres hacen match del mismo texto; por el
  desempate de ANTLR (gana la regla léxica declarada primero), todo
  literal numérico o de cadena lexea como el token genérico `Literal`, no
  como su subtipo. Por eso el tipo se decide mirando el **texto** del
  token en tiempo de análisis semántico: empieza con `"` → `string`;
  contiene `.` → `float`; si no, `integer`.
- **`visitPrimaryExpr`**: tiene que manejar `'(' expression ')'` a mano,
  porque el `visitChildren` por defecto devolvería el tipo del *último*
  hijo, que es el token `')'` (sin tipo), no el de la expresión interna.
- **`visitLeftHandSide`**: encadena el tipo base de un identificador o
  literal a través de cada `suffixOp` (`.miembro`, `[índice]`, llamada)
  usando `_chain_base` como el mecanismo heredado descrito arriba.

Y una convención transversal en los operadores binarios con la forma
`sub (OP sub)*` (aritméticos, lógicos, relacionales — toda la cadena de
precedencia `logicalOr → logicalAnd → equality → relational → additive →
multiplicative → unary`): cuando la parte opcional `(OP sub)*` **no
aparece** (por ejemplo, una expresión que nunca usa `&&`), el método debe
ser un **cable, no un chequeo** — devolver el tipo real del único operando
tal cual, sin forzar ningún tipo. Como toda expresión atraviesa esa cadena
completa aunque no use ninguno de sus operadores, forzar `BooleanType` ahí
haría que *toda* expresión del lenguaje tipara como boolean.

## 6. Reglas semánticas implementadas

### 6.1 Ámbito y declaraciones

`visitBlock` abre un `Scope` de tipo `BLOCK` por cada `{ ... }`.
`visitVariableDeclaration` declara en el ámbito actual (error si el
nombre ya existe *en ese mismo ámbito*), usa la anotación si existe o
infiere del inicializador, y si no hay ninguna de las dos queda en
`UnknownType` hasta la primera asignación. `visitIdentifierExpr` es la
lectura: `resolve` por la cadena de ámbitos, error si no existe.
`visitConstantDeclaration` es análogo pero la gramática obliga
`= expression`, así que la inicialización obligatoria de constantes sale
gratis de la sintaxis, y el tipo queda fijo. `visitClassDeclaration` abre
un `Scope` de tipo `CLASS` para sus miembros (evita choques con variables
del ámbito contenedor), valida la clase base si hereda, y apunta
`ClassType.members` al **mismo** diccionario del ámbito (no una copia)
para que `this.campo` resuelva mientras el cuerpo todavía se está
visitando.

### 6.2 Sistema de tipos y funciones

Aritméticos: ambos operandos `integer`/`float`, con promoción a `float`;
`+` también concatena `string + string`. Lógicos: `boolean`. Relacionales:
numéricos. Igualdad: tipos compatibles en cualquier dirección. Ternario:
condición `boolean`, ramas compatibles, resultado el tipo más general.
Una constante no puede reasignarse (el `Symbol.kind` lo distingue de una
variable). Una función no-`void` debe retornar en todos sus caminos
(`_always_returns`, con las limitaciones descritas en §8). La asignación
está implementada en dos métodos porque la gramática la parte en dos:
`x = 5;` es la sentencia `assignment`, pero `arr[0] = 5;` no matchea
ninguna de sus alternativas y cae en `expressionStatement →
assignmentExpr` (`visitAssignExpr`) — ambos caminos tratan igual el
narrowing de `UnknownType`. Las funciones se declaran en el ámbito
**contenedor**, antes de entrar a su propio ámbito, para que la recursión
resuelva su propio nombre; redeclarar es error porque no hay sobrecarga.

### 6.3 Control de flujo, clases y arreglos

**Condiciones booleanas.** `if`/`while`/`do-while`/`for` comparten la misma
forma: visitar la expresión de condición y reportar si el tipo devuelto no
es `BooleanType` ni `ErrorType` (se excluye `ErrorType` para no encadenar
sobre un error ya reportado). `do-while` visita el cuerpo *antes* que la
condición, siguiendo el orden real de ejecución (`do { ... } while (cond)`
ejecuta el cuerpo una vez sí o sí). `for` abre su propio `Scope` de tipo
`BLOCK` alrededor de sus tres cláusulas y el cuerpo, para que
`for (let i = 0; ...)` no filtre `i` al ámbito contenedor.

`switch` es distinto: no exige que su expresión sea `boolean`, sino que
cada `case` sea comparable con ella:

```python
def visitSwitchStatement(self, ctx: CompiscriptParser.SwitchStatementContext):
    switch_type = self._visit_type(ctx.expression())
    for case_ctx in ctx.switchCase():
        case_type = self._visit_type(case_ctx.expression())
        if (
            not isinstance(switch_type, ErrorType)
            and not isinstance(case_type, ErrorType)
            and not case_type.is_assignable_to(switch_type)
            and not switch_type.is_assignable_to(case_type)
        ):
            self._error(
                case_ctx,
                f"el tipo de 'case' ({case_type}) no es compatible con el de 'switch' ({switch_type})",
            )
```

La comprobación es en **ambas direcciones** (`case_type.is_assignable_to(switch_type)
or switch_type.is_assignable_to(case_type)`) para que `switch (unEntero) { case unFloat: ... }`
siga siendo válido gracias a la promoción `integer → float`, sin importar
de qué lado quedó el tipo más específico.

**`break`/`continue`** reportan si `_loop_depth == 0` (ver §5.2). **`return`
fuera de función** es la primera condición de `visitReturnStatement`: si
`_function_return_stack` está vacía, no hay función alrededor.

**Código muerto.** `visitBlock` recorre sus sentencias con una bandera
`unreachable`; en cuanto visita un `return`/`break`/`continue`, la
prendemos, y cualquier sentencia siguiente **en ese mismo bloque** dispara
un solo error (`código muerto: esta instrucción nunca se ejecuta`), no uno
por línea — visitar esa sentencia sigue ocurriendo (para no perder otros
errores que contenga), solo se reporta la inalcanzabilidad una vez por
región. Por diseño esto no se propaga fuera del bloque que la contiene
(ver limitación en §11).

**Acceso `.` — lectura y escritura.** La lectura (`visitPropertyAccessExpr`)
y la escritura comparten la resolución de miembros, pero la escritura
necesita conectarse a **dos** alternativas distintas de la gramática,
porque `obj.campo = valor;` matchea la sentencia `assignment`
directamente, mientras que una cadena más larga como `a.b.c = valor;` (el
lado izquierdo trae sufijos) o una asignación dentro de una expresión
mayor cae en la alternativa etiquetada `PropertyAssignExpr`. Ambas
delegan en el mismo helper:

```python
def _check_property_assignment(self, ctx, target_ctx, name, value_ctx) -> Type:
    target_type = self._visit_type(target_ctx)
    value_type = self._visit_type(value_ctx)
    if isinstance(target_type, ErrorType) or isinstance(value_type, ErrorType):
        return ErrorType()
    if not isinstance(target_type, ClassType):
        self._error(ctx, f"solo se puede asignar a miembros ('.') de un objeto; se encontró {target_type}")
        return ErrorType()

    member = self._resolve_member(target_type, name)
    if member is None:
        self._error(ctx, f"la clase '{target_type.class_name}' no tiene un miembro '{name}'")
        return ErrorType()
    if member.kind is SymbolKind.CONSTANT:
        self._error(ctx, f"no se puede asignar a '{name}': es una constante")
        return ErrorType()
    if not value_type.is_assignable_to(member.type):
        self._error(ctx, f"no se puede asignar un valor de tipo {value_type} a '{name}', de tipo {member.type}")
        return ErrorType()
    return member.type
```

`visitAssignment` (sentencia) y `visitPropertyAssignExpr` (expresión) solo
difieren en *de dónde* sacan `target_ctx`/`name`/`value_ctx` antes de
llamar a este mismo método — así el orden de validaciones (objeto → existe
→ no es constante → tipo compatible) y los mensajes de error son
idénticos sin importar qué forma sintáctica se usó. La resolución de
miembros sube por la cadena de herencia con `_resolve_member`:

```python
def _resolve_member(self, class_type: ClassType, name: str) -> Optional[Symbol]:
    node: Optional[ClassType] = class_type
    while node is not None:
        member = node.members.get(name)
        if member is not None:
            return member
        node = node.parent
    return None
```

que es también lo que usa `visitNewExpr` para encontrar el `constructor`
de una clase que hereda uno de su clase base.

**`new`** resuelve el símbolo de la clase, y si no hay `constructor`
declarado solo acepta `new C()` sin argumentos (reporta error si se le
pasa alguno); si hay `constructor`, valida aridad exacta y el tipo de cada
argumento posicionalmente contra los parámetros del `FunctionType` del
constructor. Devuelve el `ClassType` en todos los casos, incluso con
argumentos inválidos, para que un `new` mal llamado no cascadee errores
sobre todo lo que use el objeto resultante.

**`this`** reporta si no hay un `Scope` de tipo `CLASS` entre los
ancestros del ámbito actual (`self.symbols.current.enclosing(ScopeKind.CLASS) is None`);
si lo hay, no vuelve a derivarlo — simplemente devuelve el tope de
`_class_stack`, que ya quedó empujado por `visitClassDeclaration` (§5.2).

**Arreglos.** `visitArrayLiteral` sintetiza un `ArrayType` recorriendo los
elementos y acumulando un tipo resultado: si el tipo del siguiente
elemento cabe en el acumulado, sigue igual; si el acumulado cabe en el
tipo del siguiente, se ensancha (`[1, 2.5]` dan `IntegerType` y luego
`FloatType`, y como `integer` cabe en `float`, el resultado final es
`float[]`); si ninguno cabe en el otro, reporta error. Un `[]` vacío
sintetiza `ArrayType(UnknownType())`. `visitIndexExpr` exige que el
objetivo (leído de `_chain_base`, el estado heredado de la cadena, ver
§5.2) sea un `ArrayType` y que la expresión de índice sea `integer`; el
tamaño del arreglo no se valida porque no se conoce en tiempo de
compilación.

## 7. Recuperación de errores

El enunciado prohíbe detenerse en el primer error en cualquiera de las
tres fases y exige evitar mensajes repetitivos o derivados. El mecanismo
es distinto por fase:

- **Léxico**: ANTLR sigue tokenizando después de un carácter no
  reconocido; un `ErrorListener` propio (`src/error_listener.py`) registra
  el error en español con línea y columna, sin detener el proceso.
- **Sintáctico**: recuperación en modo pánico nativa de ANTLR (descarta
  tokens hasta un punto de sincronización razonable y sigue parseando).
- **Semántico**: `SemanticChecker` nunca lanza una excepción ni
  interrumpe el recorrido; cada regla que detecta un problema agrega un
  mensaje a una lista acumulada (`SemanticErrorList`) y continúa. Fue
  principio de diseño desde el reparto inicial.

Para evitar la cascada de errores derivados, toda subexpresión con un
error ya reportado devuelve `ErrorType()`, que es compatible con cualquier
tipo en las comprobaciones de asignabilidad — así el error no se
redispara en cada nodo que la contiene. El código muerto reporta un único
error por bloque inalcanzable, no uno por instrucción.

## 8. Integración con el IDE

`compiler.analyze()` devuelve `errors`, `status_message`, `tree_json` y
`symbol_table_json`. Este último es `None` (no un diccionario vacío)
cuando el análisis semántico no llegó a correr, para que el frontend
distinga "no hay símbolos" de "no se llegó hasta ahí". `server.py` lo
expone en `/api/run`; el frontend consume esa respuesta con:

- **Explorador de archivos**: panel lateral con el árbol del área de
  trabajo, mecanismo de selección del archivo de entrada.
- **Editor Monaco**: con resaltado de sintaxis propio para Compiscript.
- **Panel de salida**: cada error (léxico, sintáctico o semántico)
  encontrado, más el mensaje final de estado.
- **Visor de árbol de derivación**: representación visual y colapsable
  del árbol de parseo.
- **Visor de tabla de símbolos**: cada ámbito (global, función, clase,
  bloque) anidado en árbol, recorriendo `Scope.to_dict()`, con sus
  símbolos, tipo y ubicación.

## 9. Pruebas y validación

La batería real (la que corre `make test` vía `pytest`) vive en
`src/tests/semantic/<categoria>/`, con la convención `valido_<regla>.cps`
/ `invalido_<regla>.cps` descubierta por glob desde
`test_<categoria>.py`; agregar un caso nuevo es agregar un `.cps`. Además
hay pruebas de regresión (`src/tests/test_smoke.py`) que corren cada
muestra por el pipeline completo. Aparte de esa batería "oficial", el área
de trabajo del IDE (`workspace/input/comp-semantico/`) tiene un segundo
set de archivos por categoría (`1-tipos-*.cps` ... `7-generales-*.cps`,
más `8-tabla-simbolos-valido.cps` y `comp-tabla-simbolos/demo-tabla.cps`)
pensado como demos manuales dentro del IDE, con los mismos temas.

| Carpeta (`src/tests/semantic/`) | Casos | Cubre |
|---|---|---|
| `ambito/` | 10 | resolución por bloques anidados, shadowing, no declarada, redeclaración, herencia, ámbito de `foreach` |
| `tipos/` | 11 | aritmética, lógicas, comparaciones, ternario, asignación inferida y anotada, `const`, reasignar constante |
| `funciones/` | 9 | recursión, closures, argumentos, tipo de retorno, redeclaración, invocar algo que no es función, retorno en todos los caminos, redeclaración dentro de una closure |
| `control_flujo/` | 11 | condiciones no booleanas, `switch`/`case` compatibles e incompatibles, `break`/`continue` fuera de bucle, `return` fuera de función |
| `clases/` | 11 | atributos y métodos, herencia, miembro inexistente, constructor, `this`, acceso por anotación, escritura `.` |
| `arreglos/` | 6 | tipos de elementos, índice no entero, indexar no-arreglo, arreglo vacío, invariancia |
| `generales/` | 7 | código muerto (tras `return`, `break` y `continue`), declaraciones duplicadas, expresiones sin sentido |

### 9.1 Cobertura frente al enunciado (`docs/SemanticAnalysis.md`)

Verificación regla por regla de la sección "Requerimientos" punto 2:

**Sistema de tipos** — todo cubierto con caso válido e inválido:
aritmética (`tipos/valido_aritmetica.cps` / `invalido_aritmetica.cps`),
lógicas (`tipos/valido_logicas.cps` / `generales/invalido_sumar_booleano_con_entero.cps`),
comparaciones (`tipos/invalido_condicion_logica.cps` y los casos de
`generales/`), asignaciones (`tipos/valido_asignacion_inferida.cps` /
`tipos/invalido_asignacion.cps`), inicialización obligatoria de
constantes (garantizada por la gramática: `constantDeclaration` exige
`'=' expression` — no existe una forma sintácticamente válida de omitirla,
por lo que no aplica un caso inválido dedicado), y tipos en arreglos
(cubierto íntegramente por la categoría `arreglos/`, no hay casos
duplicados dentro de `tipos/`).

**Manejo de ámbito** — todo cubierto: resolución local/global
(`ambito/valido_resolucion_bloques_anidados.cps`), variables no
declaradas (`ambito/invalido_variable_no_declarada.cps`), redeclaración en
el mismo ámbito (`ambito/invalido_redeclaracion_mismo_ambito.cps`) vs.
shadowing legal en bloques anidados
(`ambito/valido_shadowing_en_bloque_anidado.cps`), acceso en bloques
anidados (`ambito/invalido_variable_fuera_de_bloque.cps`), y un ámbito
nuevo por función/clase/bloque (estructural — no aplica un caso "inválido"
porque no es una condición de error, se verifica por inspección de la
tabla de símbolos generada).

**Funciones y procedimientos** — cubierto: aridad y tipo de argumentos
(`funciones/invalido_argumentos.cps`), tipo de retorno
(`funciones/invalido_tipo_retorno.cps`), recursión
(`funciones/valido_recursion_y_tipos.cps`), closures
(`funciones/valido_closure.cps`), redeclaración sin sobrecarga
(`funciones/invalido_redeclaracion.cps`), y el caso inválido de una
función anidada que redeclara un nombre de su propio ámbito
(`funciones/invalido_closure_redeclaracion.cps`).

**Control de flujo** — cubierto, con un hueco real que se detectó y cerró
en esta misma revisión: condiciones booleanas de `if`/`while`
(`control_flujo/invalido_condicion_if_no_boolean.cps`,
`invalido_condicion_while_no_boolean.cps`), `break`/`continue` fuera de
bucle (`invalido_break_fuera_de_bucle.cps`,
`invalido_continue_fuera_de_bucle.cps`), `return` fuera de función
(`invalido_return_fuera_de_funcion.cps`). **`switch`/`case` no tenía
ningún caso de prueba en la batería oficial** — la regla está implementada
en `checker.py` (ver §6.3) y sí se usaba en los archivos de demostración
del IDE (`workspace/input/comp-semantico/4-control-flujo-*.cps`), pero
esos no corren con `pytest`. Se agregaron
`control_flujo/valido_switch.cps` e
`control_flujo/invalido_switch_case_incompatible.cps` para cerrarlo.

**Clases y objetos** — todo cubierto: miembros por `.`
(`clases/invalido_miembro_no_declarado.cps`,
`invalido_propiedad_no_existe_escritura.cps`), constructor
(`clases/invalido_argumentos_constructor.cps`), `this` fuera de clase
(`clases/invalido_this_fuera_de_clase.cps`).

**Listas y estructuras de datos** — todo cubierto: tipos de elementos
(`arreglos/invalido_elementos_incompatibles.cps`,
`invalido_arreglo_invariante.cps`), índices
(`arreglos/invalido_indice_no_entero.cps`,
`invalido_indexar_no_arreglo.cps`).

**Generales** — cubierto en su totalidad: código muerto tras `return`
(`generales/invalido_codigo_muerto.cps`), tras `break`
(`generales/invalido_codigo_muerto_break.cps`) y tras `continue`
(`generales/invalido_codigo_muerto_continue.cps`); expresiones sin sentido
semántico (`generales/invalido_multiplicar_funcion.cps`); declaraciones
duplicadas (`generales/invalido_declaraciones_duplicadas.cps`).

Con esto, los tres huecos detectados en la revisión de esta cobertura
quedaron cerrados con cinco archivos nuevos
(`generales/invalido_codigo_muerto_break.cps`,
`generales/invalido_codigo_muerto_continue.cps`,
`funciones/invalido_closure_redeclaracion.cps`,
`control_flujo/valido_switch.cps` e
`control_flujo/invalido_switch_case_incompatible.cps`); no queda ninguna
regla del enunciado sin al menos un caso de prueba real en la batería que
efectivamente corre `pytest`.

La suite completa (incluyendo `test_smoke.py` y las pruebas de la
extensión de `float`) ejecuta 93 pruebas, todas en verde (`make test`).

**Lo que esta batería *no* cubre**, para ser honestos sobre el alcance:
el endpoint HTTP (`server.py`) y el frontend del IDE no tienen ninguna
prueba automatizada — su verificación fue manual (correr el IDE, subir un
archivo, mirar los paneles). El enunciado no exige tests de interfaz, así
que no es un incumplimiento, pero tampoco hay evidencia reproducible más
allá de la inspección visual.

## 10. Decisiones de diseño

| Decisión | Resolución |
|---|---|
| `float` no existía en la gramática heredada pero el enunciado lo exige | Se extendió la gramática antes de repartir el trabajo: `float` en `baseType` + `FloatLiteral` |
| Listener vs Visitor | **Visitor** — cada `visit` devuelve el `Type` del nodo (ver §5.1) |
| `let x = 5;` sin anotación | El tipo se infiere del inicializador; sin inicializador queda `unknown` hasta la primera asignación |
| `null` | Asignable a arreglos y clases; nunca a primitivos |
| Sobrecarga de funciones | **No soportada** — redeclarar con el mismo nombre es error |
| Promoción numérica | `integer` → `float`, nunca al revés |
| `string + string` | Permitido (el propio lenguaje lo usa en sus ejemplos, p. ej. `"Hola " + nombre`) |
| Arreglos | **Invariantes** para tipos reales (soundness ante aliasing) |
| `[]` vacío | Entra en cualquier arreglo, pero no estrecha el símbolo permanentemente |
| Índices de arreglo | Solo se valida el **tipo** del índice; el tamaño no se conoce estáticamente |
| `new` con argumentos inválidos | Devuelve igual el `ClassType`, para no cascadear el error |
| `try`/`catch` | Fuera de alcance por decisión de equipo; el método existe como passthrough explícito |
| Idioma de los mensajes | Español, con línea y columna, mismo estilo en las tres fases |
| Declarar antes de visitar el inicializador | `let x = x + 1;` resuelve la `x` del lado derecho a la nueva declaración en vez de reportar "no declarada" — comportamiento reconocido, no un caso resuelto de forma definitiva |

## 11. Limitaciones conocidas

- **No hay hoisting.** Una función o clase usada antes de su declaración
  no resuelve, porque declarar es un efecto de visitar el nodo en orden.
  Se arreglaría con una pasada previa que registre las declaraciones de
  nivel superior antes de revisar los cuerpos.
- **`_resolve_type_node` no reporta clases no declaradas**
  (`let x: Foo;` con `Foo` inexistente pasa en silencio), consecuencia
  directa de no tener hoisting: reportarlo daría falsos positivos sobre
  clases declaradas más abajo en el archivo.
- **El código muerto no se propaga fuera de un bloque anidado.** En
  `{ return 1; } print("x");`, el `print` es inalcanzable pero no se
  reporta, porque el bloque externo ve un statement de tipo `block`, no un
  `return` directo. Lo mismo con un `if`/`else` donde ambas ramas
  retornan. Detectarlo requeriría análisis de alcanzabilidad recursivo.
- **El análisis de retorno garantizado es conservador.**
  `_always_returns` solo reconoce las formas que la gramática garantiza
  estáticamente: un `return`, un bloque que contiene uno, y un `if`/`else`
  donde ambas ramas retornan. Un bucle nunca cuenta (su cuerpo puede
  ejecutarse cero veces), así que `while (true) { return 1; }` se reporta
  como "no garantiza retorno" aunque en la práctica siempre retorne.
- **No se valida la sobreescritura de métodos** en una subclase.
- **`ClassType.__eq__` compara solo por nombre**, así que dos clases
  homónimas declaradas en ámbitos distintos se tratarían como el mismo
  tipo.

## 12. Conclusiones

1. El sistema de tipos (con promoción numérica, `ErrorType` para evitar
   cascadas y `UnknownType` para inferencia diferida) junto con una tabla
   de símbolos organizada como árbol permanente de ámbitos permitió
   implementar la totalidad de las reglas semánticas especificadas por el
   enunciado, sin reescribir la base léxica/sintáctica heredada.
2. Las tres restricciones obligatorias del enunciado se verificaron de
   forma empírica: recuperación de errores en las tres fases sin mensajes
   repetitivos o derivados, uso de una herramienta generadora (ANTLR4), e
   interfaz gráfica desde la que se selecciona el archivo de entrada y se
   visualizan errores, árbol de derivación y tabla de símbolos.
3. Dividir el trabajo por categorías de reglas semánticas —y no por los
   componentes de la ponderación— permitió avanzar en paralelo desde el
   reparto inicial sobre una interfaz común (`types.py`/`symbols.py`)
   acordada de antemano. Esas dos estructuras se diseñaron para
   reutilizarse sin cambios estructurales en las siguientes entregas del
   curso: generación de código intermedio (TAC) y de código ensamblador
   MIPS.
