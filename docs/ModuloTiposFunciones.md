# Módulo: Sistema de Tipos + Funciones

Documentación de las reglas de tipos y funciones implementadas en
`src/semantic/checker.py`, más el ajuste de `src/semantic/types.py` (ver
[plan-proyecto1.md](./plan-proyecto1.md) para la división de tareas
completa del equipo, y [ModuloAmbito.md](./ModuloAmbito.md) para la tabla
de símbolos de Persona 1, que este módulo usa directamente).

## 1. Infraestructura que no era de nadie, pero hacía falta

Ninguna de estas tres reglas estaba en la división original del Fase 0,
pero sin ellas ningún tipo se propaga por el árbol:

- **`visitLiteralExpr`**: `123`, `3.14`, `"texto"` lexean todos como el
  mismo token genérico `Literal` (ver nota abajo), así que el tipo
  concreto se determina inspeccionando el texto del literal, no el tipo
  de token.
- **`visitPrimaryExpr`**: sin esto, `(x + 1)` (expresión entre
  paréntesis) devolvía `None` — el `visitChildren` por defecto de ANTLR
  agrega tomando el resultado del *último* hijo, que para este caso es el
  token `')'`.
- **`visitLeftHandSide`**: encadena el tipo "base" a través de una cadena
  de `suffixOp` (`foo(1,2)`, `obj.campo`, `arr[0]`, o combinaciones como
  `obj.metodo(1).campo`) usando `self._chain_base` — cada `suffixOp` (una
  llamada, un índice, un acceso a propiedad) necesita el tipo de *lo que
  vino antes en la cadena*, que no está disponible en su propio nodo del
  árbol. Persona 3 debe leer `self._chain_base` al inicio de
  `visitIndexExpr`/`visitPropertyAccessExpr`, antes de visitar cualquier
  subárbol que pueda pisarlo (ver el comentario en el código).

### Nota sobre `Literal` vs `IntegerLiteral`/`FloatLiteral`/`StringLiteral`

La gramática declara `Literal: IntegerLiteral | FloatLiteral | StringLiteral;`
*antes* que esas tres reglas, y todas hacen match del mismo texto — por la
regla de desempate de ANTLR (la primera declarada gana en un empate),
**todo literal numérico o de cadena lexea como el token genérico
`Literal`**, nunca como los específicos. Es un detalle preexistente de la
gramática oficial (no introducido en este proyecto). `visitLiteralExpr` lo
resuelve mirando el texto: empieza con `"` → `string`; contiene `.` →
`float`; si no, `integer`.

## 2. `_visit_type`: por qué existe

Mientras Persona 3 no termine sus reglas (arreglos, `new`, índices, acceso
a propiedades), `self.visit(...)` sobre esas partes del árbol devuelve
`None` (el comportamiento por defecto de ANTLR), no `ErrorType`. Varias
reglas de este módulo llaman `.is_assignable_to(...)` inmediatamente
después de visitar una subexpresión — sin protección, un `None` ahí
provoca un `AttributeError` y tumba el análisis completo de cualquier
archivo que combine, por ejemplo, una declaración con arreglo con una regla
de tipos más adelante (así se descubrió: `media-val.cps`, que sí usa
arreglos, rompía el smoke test).

`_visit_type(ctx)` es el punto de entrada usado en su lugar en todo este
módulo: llama a `self.visit(ctx)` y convierte `None` en `ErrorType()`,
exactamente el mismo "no encontrado, no cascadear" que ya se usa para los
errores propios. Según Persona 3 vaya implementando sus reglas, este
`None` deja de aparecer — no hace falta tocar `_visit_type` en ese momento.

## 3. Sistema de tipos

- **Aritmética** (`+ - * /  %`): ambos operandos deben ser `integer` o
  `float`; si alguno es `float`, el resultado es `float` (promoción, nunca
  al revés). `+` también concatena `string + string` — necesario porque el
  propio `docs/DefinicionCompiscript.md` usa `"Hola " + nombre` como
  ejemplo del lenguaje.
- **Lógicas** (`&& || !`): operandos deben ser `boolean`.
- **Comparaciones** (`< <= > >=`): operandos numéricos; (`== !=`):
  operandos de tipos compatibles (`is_assignable_to` en cualquier
  dirección, para permitir comparar `integer` con `float`, o `null` con un
  tipo referencia).
- **Ternario** (`cond ? a : b`): la condición debe ser `boolean`; las dos
  ramas deben ser compatibles entre sí — el tipo resultante es el más
  general de los dos (por ejemplo `integer ? : float` da `float`).
- **Asignaciones**: `visitAssignExpr` (forma de expresión, cubre además
  `arr[0] = valor;` como sentencia — ver más abajo) y las dos secciones
  que se coordinaron con `visitVariableDeclaration`/`visitAssignment` de
  Persona 1 (sección 5). El valor debe ser asignable al tipo declarado; si
  el símbolo era `UnknownType` (sin anotación), su tipo se fija ahí, para
  siempre.
- **`const` inicializada**: la gramática ya obliga el `= expression` en
  `constantDeclaration` (no es opcional como en `variableDeclaration`), así
  que "debe inicializarse" sale gratis — `visitConstantDeclaration` se
  encarga de declarar el símbolo y verificar el tipo.

### Un detalle importante de la gramática: `assignmentExpr` es más general que `assignment`

`assignmentExpr` (la forma de expresión, `lhs=leftHandSide '=' assignmentExpr`)
acepta cualquier `leftHandSide`, incluyendo uno con `suffixOp` como
`arr[0]`. La regla de sentencia `assignment` (Persona 1) solo cubre
`Identifier '=' expression ';'` o `expression '.' Identifier '=' expression ';'`
— ninguna de las dos matchea `arr[0] = 5;`. Por eso `arr[0] = 5;` como
sentencia independiente en realidad se parsea vía
`expressionStatement -> expression -> assignmentExpr -> AssignExpr`, es
decir, por `visitAssignExpr` (este módulo), no por `visitAssignment`.

## 4. Funciones

- **Declaración**: se construye un `FunctionType(params, retorno)` y se
  declara el símbolo en el **scope que contiene** la declaración, *antes*
  de entrar al scope propio de la función — así una llamada recursiva
  dentro del cuerpo resuelve su propio nombre, y también se puede llamar
  desde afuera después.
- **Sin sobrecarga**: redeclarar un nombre de función en el mismo scope es
  error (decisión del equipo, ver `docs/plan-proyecto1.md`).
- **Parámetros sin anotación**: un parámetro sin `: type` recibe
  `UnknownType`, que acepta cualquier argumento — para esto se agregó un
  caso a `Type.is_assignable_to` en `types.py` (`target` es `UnknownType`
  → siempre asignable), el único cambio hecho a ese archivo.
- **Llamadas** (`visitCallExpr`): valida aridad (número de argumentos) y
  tipo posicional de cada uno contra el `FunctionType` del callee. El tipo
  del callee llega vía `self._chain_base` (ver sección 1).
- **Retorno**: el tipo de la expresión de `return` debe ser asignable al
  tipo de retorno declarado de la función activa — se seguimiento con
  `self._function_return_stack` (una pila simple, empujada/sacada en
  `visitFunctionDeclaration`). Sin anotación de retorno, el tipo esperado
  es `VoidType()` — `return valor;` en una función sin tipo de retorno
  reporta error igual que un tipo incompatible cualquiera.
- **Recursión y closures**: no necesitaron código especial — salen gratis
  de la cadena normal de scopes (`Scope.parent`) que ya provee la tabla de
  símbolos de Persona 1. Cubierto por
  `src/tests/semantic/funciones/valido_recursion_y_tipos.cps` y
  `valido_closure.cps`.

## 5. Coordinación con Persona 1 (resuelta)

Persona 1 dejó dos `TODO(coordinate with Persona 2)` explícitos en su
código, documentados también en la sección 6 de `ModuloAmbito.md`. Una vez
que ella terminó su parte, se cerraron ambos (cambios mínimos, sin tocar
el resto de sus métodos):

- **`visitVariableDeclaration`**: cuando hay `initializer` pero no
  `typeAnnotation`, el tipo se infiere visitando la expresión (en vez de
  quedarse siempre en `UnknownType`). Cuando sí hay anotación, se verifica
  que el valor inicial sea asignable a ese tipo.
- **`visitAssignment`** (forma `x = valor;`): se agregó la verificación de
  tipo (valor asignable al tipo del símbolo) y el narrowing de
  `UnknownType` en la primera asignación — misma lógica que
  `visitAssignExpr`, sin duplicar el mensaje de error.

## 6. Cobertura de tests

- `src/tests/semantic/tipos/` (10 casos): aritmética, lógicas,
  comparaciones, ternario, asignación inferida y con anotación (ambas
  formas: expresión y sentencia plana), declaración con tipo no
  coincidente.
- `src/tests/semantic/funciones/` (6 casos): recursión, closures,
  argumentos (número y tipo), tipo de retorno, redeclaración, llamar algo
  que no es una función.
- `src/tests/semantic/generales/` (2 casos, compartida con Persona 3):
  expresiones sin sentido semántico (multiplicar una función, sumar un
  boolean con un integer) — el chequeo numérico de
  `additiveExpr`/`multiplicativeExpr` ya las rechaza sin necesitar una
  regla nueva.

Se corren junto con el resto de la suite con:

```
make test
```

## 7. Limitaciones conocidas

- El mensaje de "solo se puede invocar una función" no distingue entre
  "esto nunca fue una función" y "esto es parte de una regla de Persona 3
  todavía sin implementar" — ambos casos hoy se ven iguales desde este
  módulo.
- No se valida que un tipo de clase usado como parámetro/retorno
  (`function f(): Persona`) corresponda a una clase realmente declarada —
  mismo límite ya documentado por Persona 1 para `_resolve_type_node`.
