# Módulo: Tabla de Símbolos + Ámbito (Persona 1)

Documentación de `src/semantic/symbols.py` y de las reglas de ámbito
implementadas en `src/semantic/checker.py` (ver
[plan-proyecto1.md](./plan-proyecto1.md) para la división de tareas
completa del equipo).

## 1. Estructuras de datos (`symbols.py`)

### `SymbolKind`

Enumera qué tipo de entidad representa un símbolo: `VARIABLE`,
`CONSTANT`, `PARAMETER`, `FUNCTION`, `CLASS`. `let` y `var` son dos
formas sintácticas de lo mismo en la gramática, así que ambas declaran
un símbolo `VARIABLE` — no hay un kind separado para cada una.

### `Symbol`

Representa un nombre declarado: `name`, `kind`, `type` (un `Type` de
`types.py`), y la posición (`line`, `column`) donde se declaró, usada
para mensajes de error. También reserva un campo `address`, sin usar
en este proyecto, pensado para las fases 2 (TAC) y 3 (MIPS) del curso.

### `ScopeKind`

Enumera el tipo de ámbito: `GLOBAL`, `FUNCTION`, `CLASS`, `BLOCK`.
Se usa para que otras reglas puedan preguntar "¿estoy dentro de una
función?" o "¿estoy dentro de una clase?" caminando hacia arriba por
la cadena de scopes (por ejemplo, la regla de `this` de Persona 3 usa
esto para validar que `this` solo se use dentro de una clase).

### `Scope`

Un ámbito individual: tiene su propia tabla de símbolos local (un
diccionario nombre → `Symbol`) y una referencia a su `parent` (el
scope que lo contiene léxicamente, o `None` para el scope global).

- `declare(symbol)`: agrega el símbolo al scope **actual únicamente**.
  Devuelve `False` si el nombre ya existe en ese mismo scope (sin
  mirar los padres) — así es como se detecta la redeclaración
  prohibida sin bloquear el shadowing en scopes anidados.
- `resolve_local(name)`: busca solo en este scope, sin subir a los
  padres. Es lo que usa `declare` internamente.
- `resolve(name)`: busca en este scope y, si no lo encuentra, sube por
  la cadena de `parent` hasta el scope global. Esto es lo que hace que
  la resolución de nombres funcione automáticamente a través de
  bloques anidados y closures, sin necesidad de código especial en
  cada regla.

### `SymbolTable`

Mantiene la pila de scopes activos durante el recorrido del árbol:

- `enter_scope(kind)`: crea un nuevo `Scope` cuyo padre es el scope
  actual, y lo empuja a la pila.
- `exit_scope()`: saca el scope actual de la pila, devolviendo el
  control al scope que lo contenía.
- `current`: el scope activo en este punto del recorrido.
- `resolve(name)` / `declare(symbol)`: delegan al scope actual.

**Patrón usado en todo `checker.py`:** cada regla que abre un nuevo
ámbito (bloques, clases, `foreach`) sigue la misma forma:

```python
self.symbols.enter_scope(ScopeKind.BLOCK)
try:
    ...  # visitar lo que esté dentro del nuevo ámbito
finally:
    self.symbols.exit_scope()
```

El `try/finally` es importante: si algo dentro del bloque hace que el
recorrido se corte a medias, `exit_scope()` igual se ejecuta y la pila
de scopes no queda desbalanceada para el resto del análisis.

## 2. Reglas de ámbito implementadas (`checker.py`)

### `visitBlock` — nuevo ámbito por bloque

Cada `{ ... }` abre un `Scope` de tipo `BLOCK`. Las variables
declaradas adentro dejan de existir al salir del bloque.

### `visitVariableDeclaration` — declarar variables

Declara el símbolo en el scope actual. Si el nombre ya existe **en
ese mismo scope**, reporta error de redeclaración (el shadowing en un
scope anidado sí está permitido). El tipo se resuelve así:

- Si hay anotación de tipo (`: integer`, `: string[]`, etc.), se usa
  el helper `_resolve_type_node` (ver sección 3).
- Si no hay anotación, el símbolo queda con `UnknownType` hasta que
  se le haga la primera asignación (`visitAssignExpr`, de Persona 2,
  narrows el tipo en ese momento).

### `visitIdentifierExpr` — leer una variable

El lado de lectura: resuelve el nombre por la cadena de scopes
(`resolve`, no `resolve_local`, para que funcione a través de
bloques/funciones anidadas). Si no existe, reporta "variable no
declarada" y devuelve `ErrorType()` para no generar una cascada de
errores en la expresión que la contiene.

### `visitAssignment` — asignar a una variable (statement)

Cubre `x = valor;` y `obj.campo = valor;` como **instrucciones**
(distinto de `visitAssignExpr`, que es Persona 2 y solo se activa
cuando una asignación aparece anidada dentro de otra expresión, como
`print(x = 5)` — caso poco común). Para la forma plana, valida que la
variable exista antes de asignarle. Para la forma de propiedad, la
validación de que la propiedad exista es de Persona 3 (acceso `.`).

### `visitClassDeclaration` — declarar una clase

Registra el nombre de la clase en el scope actual (error si ya
existía) y abre un `Scope` de tipo `CLASS` para sus miembros — esto
es lo que hace que los atributos/métodos de una clase no choquen con
variables del scope que la contiene, ni con miembros de otras clases.
Si la clase hereda de otra (`class B: A`), se valida que la clase base
exista y se resuelve al `ClassType` correspondiente para armar la
cadena `ClassType.parent`.

### `visitForeachStatement` — ámbito del `foreach`

Valida que la expresión iterada sea un arreglo (`ArrayType`) y abre
un `Scope` de tipo `BLOCK` donde se declara la variable del ciclo con
el tipo del elemento del arreglo. Al terminar el bloque, esa variable
deja de existir — usarla afuera reporta "no declarada".

### `visitTryCatchStatement` — fuera de alcance

El equipo decidió no incluir chequeo semántico de `try`/`catch` en
este proyecto (no estaba en la división original de tareas). El
método existe como passthrough explícito, documentado en el código
para que quede claro que es una decisión y no un olvido.

## 3. Helper compartido: `_resolve_type_node`

Traduce un nodo de gramática `type` (`baseType ('[' ']')*`) a un
`Type` real de `types.py`:

- Nombres primitivos (`integer`, `float`, `boolean`, `string`) se
  mapean vía el diccionario `PRIMITIVE_TYPES`.
- Cualquier otro nombre se trata como un tipo de clase (`ClassType`).
  *Nota:* por ahora no se valida que esa clase exista realmente —
  queda como mejora futura si el equipo lo necesita.
- Cada par de corchetes `[]` envuelve el tipo resultante en un
  `ArrayType` — soporta arreglos multidimensionales (`integer[][]`)
  de forma natural, envolviendo `ArrayType` dentro de `ArrayType`.

Este helper no es exclusivo de las reglas de ámbito: Persona 2 lo usa
para tipos de parámetros/retorno de funciones, y está disponible para
lo que necesite Persona 3 en arreglos.

## 4. Decisiones de diseño relevantes

- **Orden declarar-antes-de-visitar en `visitVariableDeclaration`:**
  la variable se declara en la tabla de símbolos *antes* de visitar su
  propio inicializador. Esto significa que `let x = x + 1;` resuelve
  la `x` del lado derecho a la nueva declaración, en vez de reportar
  error. Si el equipo decide que este caso debería ser un error
  ("variable usada antes de inicializarse"), es un cambio localizado
  en ese único método.
- **`declare` vs `resolve_local` vs `resolve`:** la redeclaración
  se detecta con `resolve_local`/`declare` (solo mira el scope actual)
  para permitir shadowing; la lectura de variables usa `resolve` (sube
  por los scopes padres) para que funcione a través de bloques,
  funciones anidadas y closures sin código especial.

## 5. Cobertura de tests (`src/tests/semantic/ambito/`)

10 casos (4 válidos, 6 inválidos) verificando: resolución de nombres a
través de bloques anidados, shadowing permitido, uso de variable no
declarada (lectura y asignación), redeclaración en el mismo ámbito
(variables y clases), herencia de clases válida e inválida (clase base
no declarada), y el ámbito propio de la variable de `foreach`. Se
corren junto con el resto de la suite con:

```
make test
```

## 6. Limitaciones conocidas / coordinación pendiente

- La inferencia de tipo para `let x = <expr>;` sin anotación depende
  de que Persona 2 tenga implementada la visita de expresiones —
  mientras tanto, esos símbolos quedan con `UnknownType` hasta su
  primera asignación.
- `_resolve_type_node` no valida que un nombre de clase usado como
  tipo (`let p: Persona;`) corresponda a una clase realmente
  declarada.
- La validación de que una propiedad accedida (`obj.campo`) realmente
  exista en la clase del objeto es responsabilidad de Persona 3.