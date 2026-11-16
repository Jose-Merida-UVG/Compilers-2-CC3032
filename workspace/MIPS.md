# Código objeto (MIPS)

Guía del generador de ensamblador: qué entra, qué pasa en el medio, qué sale,
cómo leer lo que muestra el IDE y cómo se ve cada construcción del lenguaje en
MIPS. El código vive en `src/asm/`; el recorrido archivo por archivo está en
`src/asm/map.md`. El TAC y el layout (de donde salen las direcciones) están
explicados en `TAC.md`.

Si nunca has leído MIPS, empieza por `MIPS-basico.md` (registros, instrucciones,
pila y syscalls en una página).

Para verlo en acción: abrir `input/comp-mips/13-recorrido-completo.cps`,
**▶ Compilar** y mirar las pestañas `tac`, `asm` y `activación`. Desde la
terminal: `make mips FILE=workspace/input/comp-mips/09-herencia-valido.cps`.

## 1. El proceso, de principio a fin

```
.cps → léxico/sintaxis → semántico → TAC + layout → MIPS → mirilla → .s final
        (si hay un error en cualquier paso, aquí se detiene todo y no hay TAC ni MIPS)
```

El generador de MIPS (`generate_asm`) recibe **dos cosas** y nada más:

1. El **TAC** (lista de strings).
2. La **tabla de símbolos** en JSON, con tamaños, offsets y direcciones ya
   calculados por `semantic/layout.py`.

No mira el árbol sintáctico. Por dentro hace esto:

```
TAC + tabla de símbolos
   │  tac_parser.parse_tac        texto → objetos del IR con tipos (Program)
   ▼
   │  por cada función (FrameInfo + RegAlloc nuevos):
   │    prólogo
   │    split_blocks              parte el cuerpo en bloques básicos
   │    por cada instrucción:     _dispatch → sel_<Clase>(ins) → MIPS
   │    epílogo
   ▼
   │  runtime (print, memoria, strings, excepciones) + tablas de métodos
   ▼
MIPS crudo ──peephole.optimize──▶ MIPS final
```

| Paso | Archivo | Qué hace |
|------|---------|----------|
| Parsear el TAC | `tac_parser.py` | Convierte cada línea en un objeto del IR (`Binary`, `Call`, `Copy`...) y deduce el tipo de cada temporal, porque el TAC no los trae. Si tiene que adivinar algo, `generate_asm` falla en vez de generar código con tipos inventados. |
| Marco de cada función | `frames.py` | Decide en qué dirección de memoria vive cada variable y temporal, y escribe el prólogo y el epílogo. |
| Recorrido | `generator.py` | Parte cada función en bloques básicos, le avisa al asignador qué instrucción viene y decide cuándo se guardan los registros a memoria. |
| Registros | `regalloc.py` | `getReg`: qué valor ocupa qué registro y cuándo se derrama a memoria. |
| Traducción | `sel_*.py` | Un *selector* (`sel_Binary`, `sel_Call`...) por instrucción del IR; escribe el MIPS. |
| Rutinas fijas | `runtime.py`, `runtime_exc.py` | `print`, `rt_alloc`, arreglos, strings y excepciones, escritas en MIPS. |
| Optimización | `peephole.py` | Mirilla: 10 reglas sobre el MIPS ya generado. |
| Datos del IDE | `activation.py` | Marcos y árbol de activación. |

## 2. Qué entra

### El TAC

```
function dbl(x: integer): integer { return x * 2; }
let a: integer = 5;
let b = dbl(a) + 1;
print(b);
```
```
func dbl(x):                  func __main():
    $t1 = x * 2                   a = 5
    return $t1                    param a
endfunc                           $t1 = call dbl, 1
                                  $t1 = $t1 + 1
                                  b = $t1
                                  print b
                              endfunc
```

El código suelto del programa queda agrupado en la función `__main`. Los `$tN`
son temporales **del TAC**; no son los registros `$t0-$t9` de MIPS (el IDE
muestra los dos y conviene no confundirlos: `$t1` del TAC puede vivir en el
registro `$t0`).

### La tabla de símbolos

Un árbol de ámbitos: cada función, bloque `{ }` y clase es un nodo.

```
GLOBAL        symbols: dbl (FUNCTION), a, b (gp+0, gp+4)      frame de __main
 └ FUNCTION dbl   symbols: x (PARAMETER, fp+8)
     │            frame {params_size, locals_size, temps, temps_size, saved_size, total_size}
     └ BLOCK      symbols: las locales (fp-4, fp-8, ...)
         └ BLOCK ...        un bloque anidado sigue numerando donde quedó su padre
 └ CLASS A        layout {size, parent, fields[name, offset, size], methods, vtable[slot, label]}
     └ FUNCTION m ...       los métodos reciben `this` como parámetro 0
```

Cada símbolo trae `name, kind, type, size, offset, address, label, tac_name`.
`type` es un string (`"integer"`, `"float[]"`, `"(integer) -> integer"`);
`address` dice dónde vive (`gp+4`, `fp+8`, `fp-4`, `this+8`); `label` es el
nombre de la función en el TAC (dos funciones anidadas con el mismo nombre
reciben etiquetas distintas: `g` y `g_1`).

**Todos los tamaños se conocen al compilar.** El P2 los calcula y el generador
solo los lee. La única memoria dinámica son los arreglos, strings y objetos,
que viven en el heap; la variable que los guarda siempre es una palabra con un
puntero.

## 3. Qué sale y cómo leerlo

`generate_asm` devuelve un `AsmResult`:

| Campo | Contenido | Dónde se ve |
|-------|-----------|-------------|
| `lines` | El MIPS crudo, sin mirilla | pestaña **asm** (botón *Sin mirilla*) |
| (después de la mirilla) | El MIPS final | pestaña **asm** |
| `activation` | Marcos de cada función y árbol de llamadas | pestaña **activación** |
| `regalloc_steps` | Por cada instrucción TAC: las decisiones de `getReg` (valor, registro, razón) y el estado de los registros al terminar | pestaña **registros** |

El `.s` tiene `.data` primero (globales, strings, floats, tablas de métodos,
variables del runtime) y `.text` después. Cada instrucción del TAC deja un
comentario `# TAC: ...` encima de su código, así que se lee de arriba hacia
abajo como "esto del TAC se tradujo a esto":

```
    # TAC: $t1 = x * y
    mul   $t2, $t0, $t1
    # TAC: $t1 = $t1 + 8
    addiu $t2, $t2, 8
```

El resumen de la mirilla (arriba del `.s`) dice cuántas instrucciones había
antes y después y cuántas veces se aplicó cada regla.

La pestaña **registros** es la tabla del asignador: una fila por instrucción TAC
con (1) cada valor que pidió, el registro que recibió y por qué (`carga`,
`en registro`, `libre`, `reuso`, `mismo registro`, `spill`, `flush`) y (2) qué
valor tiene cada registro al terminar, con `*` en los sucios (más nuevos que su
casa en memoria). Se elige la función arriba a la derecha.

La pestaña **asm** tiene *Comentarios TAC* y *Solo código*: con *Solo código*
desaparecen todos los comentarios y líneas en blanco, y lo que se copia o se
guarda con *Copiar* / *Guardar .s* es únicamente el código, listo para correr en
MARS. Sin ese botón el `.s` también corre, pero lleva los `# TAC:`.

El **registro de activación** (`activation.frames`) lista, por función, sus
casillas de direcciones altas a bajas: `param`, `saved` (`$ra`, `$fp`),
`local` y `temp`, con su dirección (`fp+8`, `fp-4`...) y tamaño. El **árbol**
(`activation.tree`) despliega las llamadas desde `__main`; una llamada
recursiva se marca `recursive` y no se despliega, una virtual se marca
`virtual`.

## 4. Modelo de memoria

Cada variable y cada temporal tiene una **casa** fija en memoria. Los
registros solo guardan una copia mientras el valor se usa.

- **`$gp`** apunta al área de globales y no cambia: las globales son `N($gp)`.
- **`$fp`** apunta al marco de la función en curso y cambia en cada llamada.
- Todo se direcciona con `$fp` o `$gp`, nunca con `$sp`, porque `$sp` se mueve
  al empujar argumentos.

```
 direcciones altas
   argumento 1     fp+12    ← los empuja quien llama, antes del jal
   argumento 0     fp+8     (en un método, el argumento 0 es `this`)
   $ra guardado    fp+4
   $fp del llamador fp+0    ← $fp apunta aquí
   local x         fp-4     ← direcciones calculadas por el P2
   local y         fp-8
   temporal $t1    fp-12    ← debajo de las locales (lo calcula frames.py)
   temporal $t2    fp-16
 direcciones bajas           ← $sp queda aquí
```

En el heap (`rt_alloc`, que devuelve memoria en cero):

```
string   .asciiz en .data            puntero a los bytes
arreglo  [longitud][e0][e1]...       4 bytes por elemento, sin importar el tipo
objeto   [tabla de métodos][campo0][campo1]...    los campos empiezan en el offset 4
tabla    vt_<Clase>: una palabra por slot con la dirección del método (en .data)
```

Un `boolean` ocupa 1 byte como campo o local, y una palabra completa como
parámetro.

## 5. Registros

**Pool del asignador:** `$t0-$t9` para enteros, booleanos y punteros;
`$f4, $f6, $f8, $f10, $f14, $f16, $f18` para floats.

**Reservados** (el asignador nunca los entrega; los selectores los usan a
mano): `$a0-$a3` y `$v0` para argumentos y resultados de las rutinas del
runtime, `$v1` y `$f12` para pasar constantes, `$f0` para devolver floats, `$at`.

### El algoritmo (`regalloc.py`, Aho §8.6.3)

- **Descriptor de registros:** qué valor tiene cada registro.
- **Descriptor de direcciones:** en qué registro está cada valor. Un registro
  *sucio* tiene un valor más nuevo que su casa en memoria.
- **Siguiente uso**, calculado hacia atrás en cada bloque. Un temporal sin uso
  futuro está *muerto*: libera su registro y no se guarda. Las variables nunca
  mueren (su casa se ve fuera del bloque).

| Método | Qué hace |
|--------|----------|
| `use(op)` | Registro con el valor de `op`; lo carga de su casa si hace falta. |
| `def_(op)` | Registro donde se calculará un resultado. Prefiere (1) el que ya tiene `op`, (2) el de un fuente que acaba de morir, (3) uno libre y (4) derramar la víctima con el uso más lejano. |
| `scratch()` | Registro anónimo hasta el fin de la instrucción. |
| `into(reg, op)` | Deja `op` en un registro fijo como `$a0`. |
| `flush()` | Guarda a su casa lo sucio que sigue vivo. |
| `invalidate()` | Olvida todos los registros (después de un `jal` o una etiqueta). |

**Por qué los fuentes se leen antes de pedir el destino:** `def_` puede
devolver el registro de un fuente muerto, así que escribir el destino antes de
leer el último fuente lo pisaría.

### Política *caller-saved* (sin `$s`)

Todo lo sucio y vivo se guarda a su casa **antes de cada salto y antes de cada
`jal`**, y después de una etiqueta o de una llamada no se confía en ningún
registro. Cada bloque empieza con los registros vacíos y termina con la
memoria al día.

- Es más simple de demostrar correcto: en cada punto de control el estado en
  memoria está completo.
- Hace seguro el `try/catch`: `rt_throw` desenrolla la pila sin restaurar
  registros, porque no hay ninguno que restaurar.
- El costo son más `sw`/`lw` en los límites de bloque. Se ve en los ejemplos de
  abajo (los `sw` justo antes de un salto). La mirilla recupera una parte.

### Traza de `getReg` en un ejemplo

```
function cuad(n: integer): integer { return n * n; }
let x: integer = cuad(3) + 1;
print(x);
```

| Instrucción TAC | Valor | Registro | Razón |
|-----------------|-------|----------|-------|
| `$t1 = n * n` | `n` | `$t0` | carga desde `8($fp)` |
| | `$t1` | `$t1` | registro libre |
| `$t1 = call cuad, 1` | `$t1` | `$t0` | libre (la llamada invalidó todo) |
| `$t1 = $t1 + 1` | `$t1` | `$t0` | el mismo registro |
| `x = $t1` | `x` | `$t0` | reuso: `$t1` murió en esta instrucción |

## 6. Cómo se ve cada construcción

Los ejemplos están recortados: sin el prólogo (`addiu $sp,-8`, guardar `$ra`
y `$fp`) ni el epílogo (restaurarlos y `jr $ra`), que son iguales en todas las
funciones. Son salidas reales del compilador.

### Declaración y asignación

```
let a: integer = 5; let s: string = "hi"; let f: float = 2.5; let b = true;
```
```
    # TAC: a = 5
    li    $t0, 5                 # entero: li
    # TAC: s = "hi"
    la    $t1, str_0             # string: la (dirección en .data)
    # TAC: f = 2.5
    l.s   $f4, flt_0             # float: l.s desde .data, registro $f
    # TAC: b = true
    li    $t2, 1
    swc1  $f4, 8($gp)            # al final del bloque cada valor va a su casa global
    sw    $t0, 0($gp)
    sw    $t1, 4($gp)
    sb    $t2, 12($gp)           # el boolean es 1 byte
```

Un valor se calcula en un registro y se guarda en su casa cuando hace falta
(antes de un salto, de una llamada o al terminar el bloque).

### Expresiones aritméticas

```
let x: integer = 2; let y: integer = 3; let z = x * y + 8; print(z);
```
```
    # TAC: $t1 = x * y
    mul   $t2, $t0, $t1
    # TAC: $t1 = $t1 + 8
    addiu $t2, $t2, 8            # constante chica: inmediato, sin cargarla
    # TAC: z = $t1
    # TAC: print z
    move  $a0, $t2
    jal   rt_print_int
```

Detalles: `x * 8` se convierte en `sll`; `/` y `%` usan `div` y leen `mflo` o
`mfhi`; los floats usan `add.s`, `mul.s`...; un entero donde se espera un float
se convierte con `mtc1` + `cvt.s.w`; `a + b` con strings llama a
`rt_str_concat`.

### Expresiones lógicas y comparaciones

Como **condición** de un salto, la comparación se traduce directo a la rama
(`blt`, `bge`, `beq`...), negándola cuando el salto es "si falso":

```
if (x < y && y != 0) { print(1); } else { print(0); }
```
```
    # TAC: if x >= y goto L2
    bge   $t0, $t1, L2
    # TAC: if y == 0 goto L2
    beq   $t0, $zero, L2         # contra cero no hace falta cargar el cero
    ...
```

`&&` y `||` se cortocircuitan: el TAC ya los parte en saltos. Como **valor**
(`let ok = x >= y;`) se usan solo instrucciones reales de MIPS:

```
    slt   $t2, $t0, $t1          # t2 = x < y
    xori  $t2, $t2, 1            # x >= y  es  !(x < y)
```

Floats: `c.lt.s` / `c.le.s` / `c.eq.s` dejan el resultado en una bandera y
`bc1t`/`bc1f` saltan. Strings: `==` llama a `rt_str_eq`, que compara contenido.

### Arreglos

```
let a: integer[] = [1, 2, 3]; let i: integer = 1; a[i] = 5; print(a[i]);
```
```
    li    $a0, 3
    jal   rt_new_array           # reserva [3][0][0][0]
    move  $t0, $v0
    ...
    # TAC: a[i] = 5
    li    $t2, 5
    lw    $t3, 0($t0)            # longitud
    sltu  $t3, $t1, $t3          # i < longitud, SIN signo: un negativo también falla
    beq   $t3, $zero, rt_throw_index
    sll   $t4, $t1, 2            # dirección = base + 4*i + 4
    addu  $t4, $t4, $t0
    sw    $t2, 4($t4)
```

Con un índice constante no se calcula la dirección: `sw $t1, 8($t0)`.

### Control de flujo

El TAC ya convirtió `if`, `while`, `for`, `foreach`, `switch`, `break` y
`continue` en etiquetas y saltos; el generador solo traduce `Label`, `Goto` y
`CondJump`.

```
while (i < 3) { s = s + i; i = i + 1; }
```
```
L1:
    lw    $t0, 0($gp)            # el bloque empieza con los registros vacíos
    li    $t1, 3
    bge   $t0, $t1, L3           # condición invertida: sale del ciclo
    ... cuerpo ...
    sw    $t0, 4($gp)            # antes del salto, lo sucio va a su casa
    sw    $t1, 0($gp)
    j     L1
L3:
```

### Funciones y parámetros

```
function dbl(x: integer): integer { return x * 2; }   print(dbl(4));
```
```
f_dbl:                           # (prólogo)
    lw    $t0, 8($fp)            # el parámetro x está en fp+8
    sll   $t1, $t0, 1            # x * 2  →  desplazamiento
    move  $v0, $t1               # el resultado va en $v0 ($f0 si es float)
f_dbl__ret:                      # (epílogo)
...
f___main:
    addiu $sp, $sp, -4           # espacio para 1 argumento
    li    $v1, 4                 # las constantes pasan por $v1: no gastan un registro
    sw    $v1, 0($sp)
    jal   f_dbl
    addiu $sp, $sp, 4
    move  $t0, $v0               # recoge el resultado
```

Secuencia de llamada: reservar los argumentos, `sw` de cada uno a `4*i($sp)`,
**flush** (todo lo sucio a su casa), `jal`, **invalidar** los registros,
liberar los argumentos y copiar `$v0`/`$f0`. Más de 4 argumentos funcionan igual
porque todos viajan por la pila.

### Recursividad

Cada activación tiene su propio marco, así que las locales y los parámetros no
se pisan:

```
function fact(n: integer): integer { if (n <= 1) { return 1; } return n * fact(n - 1); }
```
```
f_fact:
    lw    $t0, 8($fp)            # n
    li    $t1, 1
    bgt   $t0, $t1, L2
    li    $v0, 1
    j     f_fact__ret            # return 1
L2:
    lw    $t0, 8($fp)
    addiu $t1, $t0, -1           # n - 1
    addiu $sp, $sp, -4
    sw    $t1, 0($sp)            # argumento
    sw    $t1, -4($fp)           # flush antes de la llamada
    jal   f_fact
    addiu $sp, $sp, 4
    move  $t0, $v0               # el resultado vuelve en $v0
    lw    $t1, 8($fp)            # n se recarga: el registro no sobrevivió a la llamada
    mul   $t0, $t1, $t0
    move  $v0, $t0
```

El árbol de activación del IDE para `fact(3)` muestra la cadena
`__main → fact → fact → ...` con la llamada recursiva marcada.

### Clases y objetos

```
class Punto { var x: integer = 0; function sumar(): integer { return this.x; } }
let p = new Punto();
```

`new` reserva el objeto y escribe en la palabra 0 la dirección de su tabla de
métodos; el constructor sintetizado `Punto.__init_fields` asigna los valores
iniciales. Campo y método son accesos con offset del layout, y antes de usar un
objeto se verifica que no sea `null`:

```
    li    $a0, 8                 # tamaño del layout (tabla + campos)
    jal   rt_alloc
    la    $v1, vt_Perro
    sw    $v1, 0($v0)            # palabra 0: tabla de métodos
    ...
    beq   $t0, $zero, rt_throw_null     # p.x con p == null lanza "referencia nula"
    lw    $t1, 4($t0)                   # p.x: el primer campo está en el offset 4
```

### Herencia y llamadas virtuales

El hijo copia el layout del padre (los campos heredados conservan su offset) y
su tabla de métodos reutiliza el slot del padre en cada método sobrescrito.
Una llamada `a.hablar()` son tres instrucciones del TAC:

```
    $t1 = vtable a               # la tabla de métodos del objeto real
    $t1 = $t1[0]                 # el slot del método (conocido en compilación)
    $t1 = callvirt $t1, 1        # salto a esa dirección
```
```
    beq   $t0, $zero, rt_throw_null
    lw    $t1, 0($t0)            # tabla del objeto
    lw    $t1, 0($t1)            # entrada del slot 0
    addiu $sp, $sp, -4
    sw    $t0, 0($sp)            # this es el argumento 0
    ...
    jalr  $t1                    # salto a la dirección guardada en la tabla
```

Por eso `let a: Animal = new Perro()` ejecuta el `hablar` de `Perro`: la tabla
que se lee es la del objeto, no la del tipo declarado. Las tablas están en
`.data`: `vt_Perro: .word f_Perro__hablar`.

### try / catch

```
try { print(a[3]); } catch (e) { print(e); }
```
```
    la    $a0, L1
    jal   rt_try_push            # apila [dirección de L1][$sp][$fp]
    ...                          # a[3] falla: salta a rt_throw_index
    jal   rt_try_pop             # fin normal del try
    j     L2
L1:                              # el catch
    lw    $t0, exc_msg           # e = mensaje de la excepción (string)
```

`rt_throw` restaura `$sp` y `$fp` del manejador de arriba de la pila y salta a
su etiqueta. Sin manejador imprime `Excepcion no capturada: <mensaje>` y termina
con código 1. Lanzan el índice fuera de rango (`indice fuera de rango`) y el
acceso a un campo o método de `null` (`referencia nula`); el lenguaje no tiene
`throw`.

En un programa con `try`, cada instrucción guarda su resultado a su casa al
terminar: si algo lanza a mitad de un bloque, el `catch` (que empieza con los
registros vacíos) lee valores al día desde memoria.

### Funciones anidadas (closures)

Una variable de la función externa que una anidada usa no se puede alcanzar
desde el marco de esta, así que vive en una casa fija de `$gp` (`gp+N`). Como
la casa es una sola, una llamada recursiva de la externa la pisaría: el
prólogo guarda el valor previo en el marco y el epílogo lo restaura.

```
function cuenta(): integer {
  let c: integer = 10;
  function inc(): integer { c = c + 1; return c; }
  inc(); return c;
}
```
```
f_cuenta:
    ...
    lw    $v1, 0($gp)            # prólogo: valor previo de c (otra activación)
    sw    $v1, -8($fp)
    li    $t0, 10
    sw    $t0, 0($gp)            # c vive en gp+0 para que inc() lo vea
    jal   f_inc
    lw    $v0, 0($gp)
f_cuenta__ret:
    lw    $v1, -8($fp)           # epílogo: restaura el valor previo
    sw    $v1, 0($gp)
```

Dos funciones anidadas con el mismo nombre en funciones distintas (o con el
nombre de una global) reciben etiquetas distintas (`g`, `g_1`).

## 7. Mirilla (peephole)

### Qué es y por qué existe

El generador traduce **una instrucción del TAC a la vez**, sin mirar las de al
lado, así que a veces deja pequeñas ineficiencias en las costuras: un salto a la
línea que sigue, un `move` que deshace el anterior, dos ajustes de `$sp` seguidos.
La *mirilla* (peephole) es una pasada final que mira una ventana de instrucciones
contiguas del MIPS ya generado y reemplaza los patrones conocidos por algo
equivalente y más corto. Se llama así porque solo ve por un agujerito: no entiende
el programa, solo busca patrones.

Ninguna regla cambia lo que hace el programa; por eso el compilador puede mostrar
el código con y sin mirilla y los dos imprimen lo mismo.

### Cómo trabaja

- Recorre las líneas buscando cada patrón. Los comentarios `# TAC:` y las líneas en
  blanco **no cuentan** como instrucciones (se saltan); las **etiquetas sí**, porque
  alguien podría saltar a ellas y entonces las dos instrucciones ya no son vecinas
  de verdad.
- Repite hasta 5 pasadas, porque quitar algo puede dejar otro patrón al
  descubierto (por ejemplo, al quitar código muerto un salto queda justo antes de
  su etiqueta y también se quita).
- Cuenta cuántas veces aplicó cada regla; eso es lo que muestra el IDE.

### Las 10 reglas

**1. `move_redundante`** — copiar un registro a sí mismo no hace nada.
```
    move  $t0, $t0          →   (se quita)
```
**2. `salto_a_la_siguiente`** — un `j` a la línea que sigue es innecesario (pueden
mediar otras etiquetas o comentarios). Es la más frecuente: todo `return` salta al
epílogo que está justo debajo.
```
    j     f_dbl__ret                (se quita)
f_dbl__ret:                     f_dbl__ret:
```
**3. `carga_tras_guardar`** — si acabas de guardar un registro en una dirección,
cargarlo de vuelta de la misma dirección al mismo registro es inútil (también con
`swc1`/`lwc1`; con `lb` no, porque extiende el signo).
```
    sw    $t0, -4($fp)             sw    $t0, -4($fp)
    lw    $t0, -4($fp)       →     (se quita el lw)
```
**4. `guardar_tras_cargar`** — lo inverso: cargar y guardar lo mismo en la misma
dirección no cambia la memoria (no aplica si el registro es la base de la dirección,
como en `lw $t0, 0($t0)`).
```
    lw    $t0, 8($gp)              lw    $t0, 8($gp)
    sw    $t0, 8($gp)        →     (se quita el sw)
```
**5. `identidad_aritmetica`** — sumar cero, desplazar cero bits u `ori` con cero sobre el
mismo registro no hace nada: `addiu $r,$r,0`, `addu $r,$r,$zero`, `sll $r,$r,0`,
`ori $r,$r,0`. Sale de código como `(a * b) + 0`.
```
    mul   $t2, $t0, $t1             mul   $t2, $t0, $t1
    addiu $t2, $t2, 0         →     (se quita)
```
**6. `move_ida_y_vuelta`** — copiar `b` a `a` y enseguida `a` a `b` deja todo igual;
el segundo `move` sobra.
```
    move  $t0, $t1                  move  $t0, $t1
    move  $t1, $t0            →     (se quita el segundo)
```
**7. `salto_sobre_salto`** — una rama que salta una sola instrucción `j` se invierte y
absorbe el salto. Aparece en un `if` cuyo cuerpo termina en `break` o `continue`.
```
    beq   $t0, $t1, L1              bne   $t0, $t1, L2
    j     L2                  →  L1:
L1:
```
**8. `codigo_muerto`** — lo que está entre un `j`/`jr` y la siguiente etiqueta nunca
se ejecuta. Aparece con `&&` y `||`, donde el TAC deja un salto y luego código que
ya no se alcanza.
```
    j     L9                        j     L9
    li    $t0, 1             →  L1:
L1:
```
**9. `salto_a_salto`** — un salto cuyo destino es otro salto va directo al destino
final (también con `beq`/`bne`). Aparece con ifs y ciclos anidados.
```
    j     L1                        j     L2
    ...                       →     ...
L1: j     L2                    L1: j     L2
```
**10. `fusion_ajustes_sp`** — dos ajustes seguidos del puntero de pila se suman en uno
(y desaparecen si suman cero). Aparece en llamadas seguidas, donde el `+4` que libera
los argumentos de una choca con el `-4` que reserva los de la siguiente.
```
    addiu $sp, $sp, 4               (se quitan los dos)
    addiu $sp, $sp, -4
```

### Qué reglas aparecen en programas reales

El generador ya evita muchos patrones (por ejemplo, el asignador nunca emite
`move $r, $r`), así que no todas las reglas se activan con cualquier programa.
`move_redundante` y `guardar_tras_cargar` son redes de seguridad: el generador
nunca emite esos patrones (se comprobó en 75 programas), así que solo se prueban
a mano en `test_asm_peephole.py`. Las demás sí salen de programas reales y cada
una tiene su demo `17-mirilla-<regla>-valido.cps`
(prueba: `tests/asm/test_asm_peephole_demos.py`):

| Regla | Aparece en |
|-------|------------|
| `salto_a_la_siguiente` | cualquier función con `return` (por ejemplo `09-herencia-valido.cps`) |
| `salto_sobre_salto` | `if` con `break`/`continue` (`05-control_flujo-valido.cps`) |
| `codigo_muerto` | `return` dentro de `try` |
| `move_ida_y_vuelta` | llamadas anidadas, recursión |
| `salto_a_salto` | `if`/`else` dentro de un ciclo |
| `fusion_ajustes_sp` | varias llamadas seguidas con argumentos |
| `identidad_aritmetica` | `(a * b) + 0` |
| `carga_tras_guardar` | guardar un campo y leerlo enseguida (`this.x = ...; return this.x`) |

El demo **`16-mirilla-valido.cps`** reúne seis de estas reglas
(`salto_a_la_siguiente`, `salto_sobre_salto`, `salto_a_salto`, `move_ida_y_vuelta`,
`fusion_ajustes_sp` e `identidad_aritmetica`) en un programa corto y comentado.

### Cómo verlo en el IDE

1. Abrir `input/comp-mips/16-mirilla-valido.cps` y **▶ Compilar**.
2. En la pestaña **asm**, arriba del código, salen los contadores: `264 → 252
   instrucciones (−12)` y un chip por regla con las veces que se aplicó
   (`fusion_ajustes_sp ×3`, ...).
3. Los botones **Sin mirilla** y **Con mirilla** alternan entre el código original y
   el optimizado; la leyenda de abajo del resumen dice cuál se está mostrando.
4. Para ver una regla concreta, buscar el patrón del "antes" en *Sin mirilla* y
   comprobar que ya no está en *Con mirilla*. Las líneas `# TAC:` ayudan a ubicar
   dónde pasó.

Sin el IDE: `peephole.optimize(lineas)` devuelve `(líneas_nuevas, conteo_por_regla)`.

`test_asm_peephole.py` prueba cada regla, los casos donde **no** deben aplicar (una
etiqueta en medio, otra base de dirección...) y que optimizar no cambie lo que
imprime ningún programa válido.

## 8. Rúbrica: dónde está cada cosa

| Criterio (puntos) | Qué mirar | Dónde |
|-------------------|-----------|-------|
| Selección de registros (4) | `getReg`, descriptores, siguiente uso, derrames | `regalloc.py`; pestaña **registros**; demo `14-registros-valido.cps` |
| Registros y árbol de activación (5) | Marcos con `param`/`saved`/`local`/`temp` y el árbol de llamadas | `frames.py`, `activation.py`; pestaña **activación**; demo `15-activacion-valido.cps` |
| Declaración y asignación (1) | `li`/`la`/`l.s` + `sw` a la casa | `sel_core.py`; demo `01` |
| Aritmética (1) | `addu`, `mul`, `div`, `add.s`, conversión int→float | `sel_ops.py`; demo `02` |
| Lógica (1) | `slt`, ramas, cortocircuito, comparación de strings | `sel_ops.py`, `sel_control.py`; demo `03` |
| Arreglos (1) | Rango con `sltu`, `rt_new_array`, `rt_throw_index` | `sel_arrays.py`; demo `04` |
| Control de flujo (3) | `if`/`while`/`for`/`foreach`/`switch`/`break`/`continue` como saltos | `sel_control.py`; demo `05` |
| Funciones (2) | Secuencia de llamada, parámetros por la pila, retorno en `$v0` | `sel_calls.py`, `frames.py`; demo `06` |
| Recursividad (2) | Un marco por activación | demo `07` |
| Clases y objetos (2) | `rt_alloc`, offsets del layout, `null` | `sel_objects.py`; demo `08` |
| Herencia (2) | Tablas de métodos, `callvirt`, slots reutilizados | `sel_objects.py`, `emit_vtables`; demo `09` |
| try/catch (2) | Pila de manejadores, `rt_throw`, desenrollado | `sel_try.py`, `runtime_exc.py`; demo `10` |
| Mirilla, ≥ 6 transformaciones (3) | 10 reglas; el demo `16-mirilla-valido.cps` activa 6 | `peephole.py`; sección 7 |
| Simulador (1) | MARS: `src/tools/Mars4_5.jar` | `src/run_mips.py`, `make mips` |

## 9. Limitaciones conocidas

- **Closures:** si una excepción desenrolla la pila a través de una activación
  recursiva de la función externa, el valor de la variable capturada no se
  restaura (el epílogo no corre).
- **División entre cero** no lanza excepción: el resultado de `div` es
  indefinido en MARS. Sí lanzan `indice fuera de rango` y `referencia nula`.
- **Declaración antes de uso:** una función o miembro de clase debe estar
  declarado antes de usarse, así que no se puede escribir recursión mutua.
- **Arreglos de subclases mezcladas:** `[new Perro(), new Gato()]` lo rechaza el
  análisis semántico aunque el tipo declarado sea `Animal[]`.
- **El lenguaje no tiene `throw`:** las excepciones vienen solo de índices fuera
  de rango y accesos a `null`.
- **Sin `$s`:** más tráfico a memoria en los límites de bloque (ver sección 5).

## 10. Pruebas

```
make test                                  # todo
make test ARGS="src/tests/asm -q"          # solo el backend
```

- `src/tests/asm/<categoría>/`: programas `.cps` con su salida esperada `.out`,
  por cada área de la rúbrica.
- `src/tests/asm/estres_casos.py`: más de cien programas de estrés
  (herencia profunda, recursión de 20000 niveles, derrames de registros,
  closures recursivos, excepciones dentro de métodos virtuales...) con su
  salida esperada.
- `test_asm_peephole.py`, `test_asm_parser.py`, `test_asm_frames.py`,
  `test_asm_activation.py`, `test_asm_excepciones.py` y `test_asm_closures.py`:
  una por pieza.
- Los programas corren en un simulador mínimo en Python (`support/minisim.py`)
  y también en MARS real si está `src/tools/Mars4_5.jar` (`MARS_JAR`).
