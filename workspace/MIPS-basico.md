# MIPS básico (para leer lo que genera el compilador)

Guía corta de ensamblador MIPS32 tal como lo usa este proyecto en MARS. No es el
manual completo: solo lo que hace falta para leer el `.s` de la pestaña **asm**.
Después de esto, `MIPS.md` explica cómo y por qué el compilador genera cada cosa.

## 1. Qué es

El procesador ejecuta **una instrucción por línea**, de arriba hacia abajo, y cada
instrucción hace algo muy pequeño: sumar dos registros, leer una palabra de
memoria, saltar a una etiqueta. No hay variables, ni `if`, ni `while`: todo eso se
arma con registros, memoria y saltos.

Un archivo `.s` tiene dos partes:

```
        .data                   # datos: strings, floats, variables globales
str_0:  .asciiz "hola"
        .text                   # código
        .globl main
main:
    li    $t0, 5                # la ejecución empieza en `main`
```

- `etiqueta:` es un nombre para una dirección (de código o de datos).
- `#` empieza un comentario.
- `.word`, `.asciiz`, `.float`, `.space N` reservan datos; `.align 2` alinea a 4 bytes.

## 2. Registros

Un registro es una variable ultrarrápida dentro del procesador, de 32 bits. Hay 32
enteros (`$0`-`$31`) con nombres por convención, y 32 para floats (`$f0`-`$f31`).

| Registro | Para qué lo usa este compilador |
|----------|--------------------------------|
| `$zero` | Siempre vale 0 (no se puede cambiar). Sirve de constante 0 y de "no". |
| `$t0`-`$t9` | Temporales: aquí viven los valores mientras se calculan. El asignador de registros los reparte. |
| `$a0`-`$a3` | Argumentos de las rutinas del runtime (`print`, `alloc`...). |
| `$v0`, `$v1` | `$v0` devuelve resultados y elige la syscall; `$v1` pasa constantes. |
| `$sp` | Puntero de pila: la cima de la pila (crece hacia abajo). |
| `$fp` | Puntero de marco: base de la función en curso. |
| `$gp` | Base del área de variables globales. |
| `$ra` | Dirección de retorno: a dónde volver al terminar una función. |
| `$f4`, `$f6`... | Valores float (`$f0` devuelve floats, `$f12` pasa/imprime uno). |

`$t1` en MIPS **no** es el `$t1` del TAC: el TAC usa su propia numeración de
temporales y el asignador decide en qué registro real vive cada uno.

## 3. Instrucciones que vas a ver

La forma general es `operación destino, fuente1, fuente2`. El **destino va primero**.

### Constantes y copias
```
    li    $t0, 5             # t0 = 5                (load immediate)
    la    $t0, str_0         # t0 = dirección de str_0 (load address)
    move  $t1, $t0           # t1 = t0
    l.s   $f4, flt_0         # f4 = el float guardado en flt_0
```

### Aritmética
```
    addu  $t2, $t0, $t1      # t2 = t0 + t1
    addiu $t2, $t0, 8        # t2 = t0 + 8   (la `i` es "inmediato": una constante)
    subu  $t2, $t0, $t1      # t2 = t0 - t1
    mul   $t2, $t0, $t1      # t2 = t0 * t1
    sll   $t2, $t0, 2        # t2 = t0 * 4   (desplazar 2 bits a la izquierda)
    div   $t0, $t1           # divide: el cociente queda en `lo`, el residuo en `hi`
    mflo  $t2                # t2 = cociente    (move from lo)
    mfhi  $t2                # t2 = residuo     (move from hi)
    add.s $f4, $f6, $f8      # floats: add.s, sub.s, mul.s, div.s
```

### Comparaciones como valor
```
    slt   $t2, $t0, $t1      # t2 = 1 si t0 < t1, si no 0   (set on less than)
    xori  $t2, $t2, 1        # t2 = !t2     (invierte 0 y 1)
```

### Memoria
`N(reg)` significa "la dirección `reg + N`".
```
    lw    $t0, 8($fp)        # t0 = memoria[fp + 8]       (load word, 4 bytes)
    sw    $t0, 0($gp)        # memoria[gp + 0] = t0       (store word)
    lb    $t0, 0($t1)        # carga 1 byte;  sb guarda 1 byte (strings, booleanos)
    lwc1  $f4, 0($t1)        # carga un float; swc1 lo guarda
```
Una variable global `a` en `gp+0` se lee con `lw $t0, 0($gp)` y se escribe con
`sw $t0, 0($gp)`. Un parámetro en `fp+8` igual, pero con `$fp`.

### Saltos y ramas
```
    j     L1                 # salta a L1 siempre
    beq   $t0, $t1, L1       # salta si t0 == t1            (branch if equal)
    bne   $t0, $t1, L1       # salta si t0 != t1
    blt   $t0, $t1, L1       # salta si t0 <  t1   (también ble, bgt, bge)
    beq   $t0, $zero, L1     # salta si t0 == 0   (así se prueba "falso")
    bltz  $t0, L1            # salta si t0 < 0   (también blez, bgtz, bgez)
    c.lt.s $f4, $f6          # float: compara y deja una bandera...
    bc1t  L1                 # ...y salta si la bandera es verdadera (bc1f: falsa)
```
Un `if (x < y) { ... }` se convierte en: "salta *sobre* el cuerpo si `x >= y`".
Por eso en el código ves la condición **invertida**.

### Llamar a una función
```
    jal   f_dbl              # llama: guarda en $ra la línea siguiente y salta
    jr    $ra                # vuelve: salta a la dirección guardada en $ra
    jalr  $t1                # llama a la dirección que está en t1 (método virtual)
```

### Pseudoinstrucciones
`li`, `la`, `move`, `blt`, `bge`... no existen en el procesador real: MARS las
expande a una o dos instrucciones reales. En el código las escribimos tal cual.

## 4. La pila y las funciones

La **pila** es memoria que crece hacia direcciones más bajas. `$sp` apunta a su
cima. Empujar es bajar `$sp` y escribir; sacar es subir `$sp`.

Cuando una función llama a otra pasan tres cosas (el compilador lo escribe así):

```
    # quien llama
    addiu $sp, $sp, -4       # hace espacio para 1 argumento
    sw    $t0, 0($sp)        # lo guarda en la pila
    jal   f_dbl              # llama (en $ra queda la dirección de vuelta)
    addiu $sp, $sp, 4        # libera el argumento
    move  $t0, $v0           # el resultado llegó en $v0

    # la función llamada, al empezar (prólogo)
f_dbl:
    addiu $sp, $sp, -8
    sw    $ra, 4($sp)        # guarda a dónde volver
    sw    $fp, 0($sp)        # guarda el marco de quien llamó
    move  $fp, $sp           # su marco empieza aquí
    addiu $sp, $sp, -4       # espacio para sus locales y temporales
    lw    $t0, 8($fp)        # el argumento está en fp+8

    # al terminar (epílogo)
    move  $v0, $t1           # pone el resultado en $v0
    move  $sp, $fp           # deshace el marco
    lw    $ra, 4($sp)
    lw    $fp, 0($sp)
    addiu $sp, $sp, 8
    jr    $ra                # vuelve a quien llamó
```

Así cada llamada tiene su propio marco, y por eso la recursión funciona: `fact(3)`
llama a `fact(2)` y cada uno tiene su `n`.

## 5. Imprimir y terminar: syscalls

Para pedirle algo al sistema se pone un número en `$v0` y se ejecuta `syscall`.

| `$v0` | Hace | Argumento |
|-------|------|-----------|
| 1 | imprime un entero | `$a0` |
| 2 | imprime un float | `$f12` |
| 4 | imprime un string | `$a0` = dirección |
| 9 | reserva memoria en el heap (`sbrk`) | `$a0` = bytes; devuelve la dirección en `$v0` |
| 10 | termina el programa | |
| 11 | imprime un carácter | `$a0` = el código (10 = salto de línea) |
| 17 | termina con un código de salida | `$a0` |

El compilador no las escribe en cada `print`: llama a rutinas (`rt_print_int`...)
que ya las contienen, escritas una sola vez al final del archivo.

## 6. Cómo se lee una línea del compilador

```
    # TAC: $t1 = x * 2
    lw    $t0, 8($fp)        # t0 = x          (x es el parámetro 0: fp+8)
    sll   $t1, $t0, 1        # t1 = t0 * 2     (multiplicar por 2 = desplazar 1 bit)
    # TAC: return $t1
    move  $v0, $t1           # el resultado va en $v0
    j     f_dbl__ret         # salta al epílogo
```

Receta para leer cualquier trozo:
1. Mirar el `# TAC:` de arriba: qué se quería hacer.
2. Cada `lw` trae una variable de memoria a un registro; cada `sw` la devuelve.
3. Las operaciones trabajan solo entre registros.
4. Un `beq`/`bne`/`blt`... con una etiqueta es un `if` o un ciclo; buscar la etiqueta
   (`L3:`) para ver a dónde salta.
5. Un `jal` es una llamada: los argumentos se acaban de empujar a la pila justo antes.

## 7. Ejercicio

Ejecuta este programa y compáralo con el código de la pestaña **asm** (con *Solo
código* activado, queda más limpio):

```
let a: integer = 5;
let b: integer = a + 3;
print(b);
```

Encuentra: dónde se carga el 5 (`li`), la suma (`addiu`), a dónde se guarda `b`
(`sw ... ($gp)`), la llamada a `rt_print_int` y la syscall dentro de ella.
Si puedes explicar cada una de esas cuatro líneas, ya puedes leer el resto.

Referencias: la ayuda integrada de MARS (*Help → MIPS*) lista todas las
instrucciones y syscalls.
