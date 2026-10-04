# Proyecto 2 — Contrato común (LEER PRIMERO, los tres)

Entrega: **lunes 5 de octubre de 2026, 13:00**. Hoy es jueves 1. Equipo: Cami (cimientos + GUI), Nes (expresiones + control de flujo), Tono (funciones, clases, tabla de símbolos).
Alcance: léxico + sintáctico + semántico (ya hecho en el P1) **+ generación de código intermedio (TAC)**.
Base: este repo (`src/compiler.py`, `src/semantic/*`, `src/server.py`, `frontend/`). 96 tests pasan hoy (`make test`).

---

## 0. Instrucciones para la IA que lea este archivo

Este markdown se le pasa a un asistente de IA. Reglas obligatorias:

1. **Lee primero** este contrato completo y luego SOLO tu archivo (`01-nes.md`, `02-tono.md` o `03-cami.md`). Lee también el código existente que menciona tu archivo antes de editar.
2. **Revisa y pregunta antes de commitear.** No hagas `git commit`, `git push`, merge ni PR sin mostrarle antes a la persona el `git diff`/lista de archivos y recibir un "sí" explícito. Una aprobación vale solo para ese commit.
3. **Si algo es ambiguo o contradice el contrato, pregunta** a la persona; no inventes ni cambies el contrato por tu cuenta. Los cambios al contrato los acuerdan los tres humanos y se anotan en la sección 9 de este archivo.
4. **Toca únicamente los archivos que tu documento te asigna.** Si necesitas un cambio en un archivo ajeno, avísale a la persona para que lo coordine con su dueño.
5. **Commits individuales:** cada persona commitea con su propio usuario de git (el README del curso exige atribución individual, sin commits compartidos). Rama propia (`p2/nes`, `p2/tono`, `p2/cami`) salida de `proyecto2`. Mensajes en el estilo del repo (`feat:`, `fix:`, `test:`, `docs:`).
6. Corre `make test` antes de proponer un commit. No rompas los 96 tests existentes.
7. **Prohibido (se castiga con 0):** ejecutar/interpretar el programa Compiscript o generar código objeto/ensamblador. Solo se genera TAC como texto. No agregues un "intérprete de TAC".
8. Código en el mismo estilo del repo (docstrings breves, comentarios en español o inglés como el archivo vecino, tipos con `from __future__ import annotations`).

---

## 1. Requisitos del enunciado (se cumplen al pie de la letra)

| # | Requisito | Penalización si falla | Estado / dueño |
|---|---|---|---|
| R1 | Usar generador de analizadores (ANTLR) | **0 pts** | ya cumple (P1) |
| R2 | GUI amigable y estética | −5 | Cami |
| R3 | El archivo de entrada se elige desde la GUI | −5 | ya existe (FileExplorer); Cami lo mantiene |
| R4 | Resultados del análisis **y el TAC** se muestran en la GUI, no solo en consola | −5 | Cami (mostrar y producir) |
| R5 | Archivos de prueba escritos por el grupo | — | los tres, cada quien sus áreas |
| R6 | No terminar en el primer error; hay recuperación | −5 | ya existe (P1); nadie debe romperlo |
| R7 | Sin errores repetidos, sin ciclos infinitos, sin mensajes derivados inútiles | −5 | ya existe; Cami verifica en integración |
| R8 | **Si hay cualquier error (léxico/sintáctico/semántico) NO se genera TAC** | — | Cami (`compiler.py` y UI) |
| R9 | Alcance: solo análisis + TAC; no ejecutar ni producir código objeto | **0 pts** | todos |
| R10 | Documentar el lenguaje intermedio con ejemplos y justificación de diseño | rúbrica (3 pts) | Cami redacta; Nes y Tono aportan ejemplos de lo suyo |
| R11 | Repo con commits individuales | — | todos |
| R12 | Tabla de símbolos con datos para código objeto (direcciones, etiquetas, registros de activación) | rúbrica (2 pts) | Tono |
| R13 | Algoritmo de asignación y reciclaje de temporales | rúbrica (3 pts) | Cami |

Rúbrica (25 pts) y dueño: ver `README.md` de esta carpeta.

---

## 2. Arquitectura

```
fuente → Lexer/Parser (ANTLR) → SemanticChecker → [si 0 errores] → TACGenerator → TAC (texto)
                                      │                                  │
                                 symbols (Scope tree)  ──────►  layout.py (offsets, frames)  → .symbols JSON
```

Archivos nuevos (paquete `src/tac/`) y dueño. **Un archivo = un dueño**, así no hay conflictos de merge:

| Archivo | Dueño | Contenido |
|---|---|---|
| `src/tac/instructions.py` | Cami | formato de instrucciones (sección 3) |
| `src/tac/emitter.py` | Cami | `Emitter`: emit, temporales, etiquetas, unidades |
| `src/tac/generator.py` | Cami | `TACGenerator` = clase que une los mixins + helpers + `program`/`block`/`statement` (sección 4) |
| `src/tac/gen_core.py` | Nes | `CoreMixin`: declaraciones, aritmética, lógicas, arreglos, print |
| `src/tac/gen_control.py` | Nes | `ControlMixin`: if/while/do/for/foreach/switch/break/continue/try-catch |
| `src/tac/gen_functions.py` | Tono | `FunctionMixin`: funciones, llamadas, return, recursividad |
| `src/tac/gen_classes.py` | Tono | `ClassMixin`: clases, objetos, herencia |
| `src/semantic/layout.py` | Tono | offsets, tamaños, registros de activación, layout de clases |
| `src/semantic/symbols.py` | Tono | campos nuevos en `Symbol`/`Scope` y `to_dict` |
| `src/semantic/checker.py` | Cami | solo el parche de anotaciones (sección 5) |
| `src/compiler.py`, `src/main.py` | Cami | integración (sección 6) |
| `src/server.py`, `frontend/**` | Cami | API y GUI (sección 7) |
| `src/tests/conftest.py` | Cami | helper `compile_tac` y golden |
| `src/tests/tac/<area>/**`, `workspace/input/comp-tac/<area>-*.cps` | dueño del área | pruebas |

El generador es **un visitor ANTLR aparte** que corre después del checker. Cada mixin define métodos `visitXxx` de **reglas distintas** (tabla de la sección 4), por eso no se pisan.

---

## 3. Lenguaje intermedio (sintaxis fija — opción A, estilo Dragon Book)

Una instrucción por línea. Etiquetas pegadas a la izquierda terminando en `:`; instrucciones con 4 espacios de sangría; `func`/`endfunc`/`class`/`endclass` pegados a la izquierda.

**Operandos** (siempre `str`): variable (`x`, `x_1` si hay sombreado, ver 4.3), temporal `$t1`, `$t2`…, constante literal (`5`, `3.14`, `"hola"`, `true`, `false`, `null`).
Los temporales usan `$` porque no puede chocar con un identificador del usuario. Etiquetas: `L1`, `L2`… (globales al programa, numeración creciente).

| Instrucción | Significado |
|---|---|
| `x = y` | copia |
| `x = y OP z` | OP ∈ `+ - * / % == != < <= > >= ` (en string, `+` es concatenación) |
| `x = - y` , `x = ! y` | unarios |
| `x = itof y` | promoción integer→float (solo si el checker la aplica) |
| `L:` | etiqueta |
| `goto L` | salto |
| `if x goto L` , `if x REL y goto L` | salto condicional (REL como arriba) |
| `ifFalse x goto L` | salto si falso |
| `param x` | argumento (en orden, antes de `call`) |
| `x = call f, n` , `call f, n` | llamada con n parámetros (sí cuenta `this`) |
| `return x` , `return` | retorno |
| `func f(p1, p2):` … `endfunc` | definición; métodos: `func Clase.metodo(this, p1):` |
| `x = newarray n` | arreglo con n elementos |
| `x[i] = y` , `x = y[i]` , `x = len y` | arreglos |
| `x = new C` | instancia (reserva) |
| `x.f = y` , `x = y.f` | campos |
| `print x` | `print(...)` del lenguaje |
| `try Lc` / `endtry` / `catch e` | try-catch (ver `01-nes.md`) |
| `class C : P:` … `endclass` | agrupa los métodos de una clase (la cabecera lleva `: P` solo si hereda) |

Programa de nivel superior: todo código suelto va en `func __main():`, que se emite **al final**. Las funciones/métodos se emiten completos cuando terminan (las anidadas salen después de su función contenedora; el `Emitter` lo maneja con una pila de unidades).

Ejemplo completo esperado:

```
func fact(n):
    $t1 = n <= 1
    ifFalse $t1 goto L1
    return 1
L1:
    $t1 = n - 1
    param $t1
    $t1 = call fact, 1
    $t1 = n * $t1
    return $t1
endfunc
func __main():
    param 5
    $t1 = call fact, 1
    print $t1
endfunc
```

Cualquier cambio de sintaxis se negocia entre los tres y se anota en la sección 9.

---

## 4. API del generador (lo que cada mixin puede asumir)

El esqueleto lo sube **Cami primero** (paso 0, meta: jueves en la noche). Mientras tanto los demás avanzan contra esta especificación (pruebas `.cps`, diseño, mocks).

```python
# src/tac/emitter.py (Cami)
class Emitter:
    def emit(self, text: str) -> None            # agrega "    text" a la unidad actual
    def emit_label(self, label: str) -> None     # agrega "label:" sin sangría
    def new_label(self) -> str                   # "L1", "L2", ...
    def new_temp(self) -> str                    # "$tN": reutiliza uno liberado o crea nuevo
    def free(self, operand: str) -> None         # si es temporal, lo devuelve al pool; si no, no hace nada
    def begin_unit(self, header: str) -> None    # abre func/class (apila)
    def end_unit(self, footer: str) -> None      # cierra y guarda la unidad terminada
    def max_temps(self, unit_name: str) -> int   # pico de temporales simultáneos (para Tono)
    def live_temps(self) -> int                  # temporales aún ocupados (detector de fugas)
    def lines(self) -> list[str]                 # resultado final, __main al final

# src/tac/generator.py (Cami) -- TACGenerator(CoreMixin, ControlMixin, FunctionMixin, ClassMixin, CompiscriptVisitor)
self.e                      # Emitter
self.expr(ctx) -> str       # visita una expresión y devuelve su operando
self.gen_cond(ctx, ltrue, lfalse) -> None   # emite saltos: ltrue si es verdadera, lfalse si no. Siempre emite ambos saltos o cae en uno; el llamador pone las etiquetas
self.type_of(ctx) -> Type            # tipo semántico anotado por el checker
self.symbol_of(ctx) -> Symbol|None   # símbolo resuelto de un identificador/declaración
self.scope_of(ctx) -> Scope          # ámbito vigente en ese nodo
self.name_of(symbol) -> str          # nombre único del símbolo en el TAC (4.3)
self.break_labels / self.continue_labels   # pilas (list[str]); las llena Nes (ControlMixin); Tono usa return aparte
```

### 4.1 Propiedad de reglas (cada `visitXxx` lo implementa UNA sola persona)

| Dueño | Reglas de la gramática |
|---|---|
| **Cami** (en `generator.py`) | `program`, `statement` (default), `block` |
| **Nes** | `variableDeclaration`, `constantDeclaration`, `assignment`, `expressionStatement`, `printStatement`, `AssignExpr`, `ExprNoAssign`, `TernaryExpr`, `logicalOrExpr`, `logicalAndExpr`, `equalityExpr`, `relationalExpr`, `additiveExpr`, `multiplicativeExpr`, `unaryExpr`, `primaryExpr`, `literalExpr`, `arrayLiteral`, `IdentifierExpr`, `IndexExpr`, `ifStatement`, `whileStatement`, `doWhileStatement`, `forStatement`, `foreachStatement`, `switchStatement` (+`switchCase`, `defaultCase`), `breakStatement`, `continueStatement`, `tryCatchStatement` |
| **Tono** | `functionDeclaration`, `returnStatement`, `CallExpr`, `classDeclaration`, `NewExpr`, `ThisExpr`, `PropertyAccessExpr`, `PropertyAssignExpr`, `leftHandSide` (cadena de sufijos) |

Regla de oro: si tu regla necesita evaluar una expresión, **llama `self.expr(ctx)`**; si necesita saltar según una condición, **llama `self.gen_cond(...)`**. Nunca re-implementes lo del otro.
En el esqueleto, `gen_cond` tiene una implementación por defecto (evalúa con `expr`, `if t goto ltrue`, `goto lfalse`) y Nes la reemplaza por la versión con cortocircuito. Así Nes puede escribir control de flujo desde el minuto uno.

### 4.2 Propiedad de temporales (reciclaje, R13)

- Quien **consume** un operando lo libera con `self.e.free(op)` justo después de emitir la instrucción que lo usa. Luego pide el temporal del resultado: así `$t1 = $t1 + ...` reutiliza.
- Temporales que deben vivir más (índice/longitud de un `foreach`, valor de un `switch`, objeto de un `new` hasta su `call`): se liberan **explícitamente al final** de la construcción.
- Al terminar cada función, `live_temps() == 0`. Cami agrega ese assert en las pruebas; una fuga es un bug del dueño de esa regla.
- El pool se reinicia al abrir cada unidad (`begin_unit`).

### 4.3 Nombres

`name_of(symbol)` devuelve el nombre del identificador; si dos símbolos con el mismo nombre coexisten en la misma unidad (sombreado en bloques), el segundo se llama `x_1`, el tercero `x_2`… Parámetros y campos conservan su nombre. Las funciones son `f`; los métodos `Clase.metodo`; el constructor `Clase.constructor`.

---

## 5. Parche al checker (lo hace Cami, paso 0)

`SemanticChecker` hoy devuelve el `Type` de cada expresión pero no lo guarda. Se agrega:

```python
self.node_types: dict[int, Type] = {}      # id(ctx) -> Type
self.node_symbols: dict[int, Symbol] = {}  # id(ctx) -> Symbol resuelto/declarado
self.node_scopes: dict[int, Scope] = {}    # id(ctx) -> Scope vigente al entrar
```

Cami lo implementa. Se llenan en un override de `visit()` (≈10 líneas) y en los puntos donde se resuelve/declara un símbolo. Para nodos que abren ámbito propio (función, clase, bloque, for, foreach, catch) también se guarda el ámbito interno (`node_inner_scopes`). Los 96 tests no deben cambiar.

---

## 6. Integración en `compiler.analyze` (Cami)

`analyze()` agrega la clave `"tac": list[str] | None`:

- `errors` vacío → se genera TAC y se devuelve `list[str]`.
- hay errores → `None` y `status_message` actual (el TAC **no** se genera, R8).
- El `status_message` de éxito se actualiza: "…No se encontraron errores. Código intermedio generado (N instrucciones)."

`main.py` imprime el TAC si existe. Orden del símbolo table: `symbol_table_json` se genera **después** de `layout.assign_layout()` (Tono) y el TAC (para tener `max_temps`).

---

## 7. API y GUI (Cami)

`POST /api/run` devuelve además:

```json
{ "tac": ["func fact(n):", "    $t1 = n <= 1", "..."],   // null si hubo errores
  "tacStats": { "instructions": 42, "temps": 3, "functions": 2 } }   // null si tac es null
```

Se guarda `workspace/output/<stem>/<archivo>.tac`. La GUI abre un panel/pestaña **TAC** (read-only, con numeración y resaltado de etiquetas/`func`) y, si hay errores, un aviso visible "No se generó código intermedio porque hay N errores" (R4/R8).

Tabla de símbolos — campos nuevos en el JSON (Tono los produce, Cami los muestra):

```json
// por símbolo
{ "name":"x", "kind":"VARIABLE", "type":"integer", "line":3, "column":4,
  "size":4, "offset":0, "address":"fp-4", "label":null }
// por ámbito FUNCTION (además de kind/owner/symbols/children)
"frame": { "label":"fact", "params_size":4, "locals_size":8, "temps":2, "temps_size":8,
           "saved_size":8, "total_size":28 }
// por ámbito CLASS
"layout": { "size":12, "parent":"Animal",
            "fields":[{"name":"nombre","offset":0,"size":4,"inherited":true}],
            "methods":[{"name":"hablar","label":"Perro.hablar","overrides":"Animal.hablar"}] }
```

Tamaños (MIPS32): integer 4, float 4, boolean 1, string/array/instancia = referencia de 4; alineación natural.
Mientras Tono no entregue, Cami trabaja con un JSON mock (`frontend/src/mocks/`), y cambia a datos reales al integrar (todo lo del TAC lo produce ella misma; solo la tabla de símbolos nueva viene de Tono).

---

## 8. Pruebas

- Casos por área en `src/tests/tac/<area>/` con `valido_*.cps` + `valido_*.tac` (golden, texto exacto) e `invalido_*.cps` (esperan `tac is None` y errores).
- Áreas: `declaraciones`, `aritmetica`, `logicas`, `arreglos`, `control_flujo`, `funciones`, `recursividad`, `clases`, `herencia`, `try_catch`, `temporales`, `tabla_simbolos`.
- Helper `compile_tac(source) -> (errors, tac)` en `src/tests/conftest.py` (Cami, paso 0). `UPDATE_GOLDEN=1 make test` regenera los golden; **revisa a mano** el diff antes de aceptarlo.
- Cada test válido verifica además `live_temps() == 0` por función.
- Para la demo: copia de los casos en `workspace/input/comp-tac/` (`<area>-valido.cps`, `<area>-invalido.cps`).

---

## 9. Registro de cambios al contrato

(agreguen aquí fecha, quién y qué cambió; avisen a los otros dos)

**2026-10-01 · Nes (a raíz de escribir `gen_core.py`/`gen_control.py` contra el contrato):**

1. **Parche del checker:** sobrescribir solo `visit()` **no basta**: el visitor por defecto (`visitChildren`, p. ej. en `statement`) llama `child.accept()` directo y se salta `visit()`. Cami debe sobrescribir también `visitChildren` para que pase por `self.visit(child)`, o las anotaciones faltarán en declaraciones y sentencias.
2. **`symbol_of(ctx)`** se llama con: `IdentifierExpr`, `variableDeclaration`, `constantDeclaration`, `assignment` (forma simple), `foreachStatement` (variable de iteración), `tryCatchStatement` (variable del catch) y, para `AssignExpr` con identificador simple, el `leftHandSide` `lhs`. Si devuelve `None`, `gen_core` usa el texto del identificador.
3. **`gen_cond(ctx, ltrue, lfalse, fall=None)`:** parámetro opcional `fall` = etiqueta que el llamador colocará justo después. Si `fall == ltrue` solo se emite el salto a `lfalse` (y viceversa), evitando `goto` redundantes. **El `gen_cond` por defecto debe vivir en una clase base listada DESPUÉS de los mixins** (`class TACGenerator(CoreMixin, ControlMixin, FunctionMixin, ClassMixin, BaseGen, CompiscriptVisitor)`); si se define en `TACGenerator` mismo tapa la versión real de Nes.
4. **Arreglos:** `visitIndexExpr(ctx)` (Nes) devuelve el operando del **índice**; la cadena `leftHandSide` (Tono) hace `base = self.gen_index_load(base, idx)`. Nes expone `gen_index_load(base, idx) -> operando` y `gen_index_store(base, idx, val)`. Tono expone `eval_chain(lhs_ctx, n) -> operando` (evalúa `primaryAtom` más los primeros `n` sufijos); Nes lo usa en `AssignExpr` (`a.b[i] = v`) cuando el prefijo tiene llamadas/propiedades.
5. **try/catch:** `ControlMixin` mantiene `self.open_tries` (nº de `try` abiertos). Tono: antes de un `return` dentro de un `try`, emitir `endtry` `self.open_tries` veces.
6. **`void` en `expressionStatement`:** `CallExpr` (Tono) puede devolver `None` si la función es void; Nes solo libera el operando si existe.
7. **Esqueleto de Cami:** `gen_core.py` y `gen_control.py` ya existen (Nes los sube); en el paso 0 Cami no debe crearlos vacíos, o al hacer merge se queda la versión de Nes. `src/tac/__init__.py` vacío lo suben ambos (idéntico, sin conflicto).
8. **Tests:** `src/tests/tac/test_tac_golden.py` (Nes) recorre todas las carpetas `src/tests/tac/<area>/` con `valido_*.cps`+`.tac` e `invalido_*.cps` usando `analyze_file()["tac"]`; Tono y Cami solo agregan casos en su carpeta, no necesitan escribir otro test. Se saltan mientras `analyze` no devuelva la clave `tac`.

---

## 10. Cronograma

| Cuándo | Qué |
|---|---|
| Jue 1 (noche) | Cami: paso 0 (esqueleto + parche checker + `compile_tac`) en `proyecto2`. Nes y Tono: ramas creadas, `make test` verde, escriben `.cps` de prueba y los `.tac` esperados a mano. Tono arranca `layout.py`. |
| Vie 2 | Nes y Tono: su núcleo + pruebas de su área. Cami: reciclaje de temporales, integración en `compiler.py`, GUI con mocks. |
| Sáb 3 | Terminar áreas. Cami conecta GUI a datos reales y verifica R6/R7/R8. Merge a `proyecto2`. |
| Dom 4 | Pruebas cruzadas (cada quien prueba el código del otro), pulido GUI, `LenguajeIntermedio.md` y docs finales, video/demo. |
| Lun 5 | 08:00–10:00 solo bugs. **Congelar a las 10:00**; entrega antes de 13:00. |
