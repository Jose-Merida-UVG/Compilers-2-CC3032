# Guía de `recorrido-completo.cps`

Qué debería salir al compilar el demo y por qué. El TAC y la tabla de símbolos de
abajo son la salida real del compilador. Para verlos: abrir `recorrido-completo.cps`
en el IDE, **▶ Compilar** y mirar las pestañas `tac` y `symbols`.

Dos cosas distintas salen del compilador, y conviene no mezclarlas:

* **TAC** (`.tac`): las instrucciones. Dice *qué* se hace y en qué orden.
* **Tabla de símbolos** (`.symbols`): dónde vive cada cosa en memoria (offsets,
  frames, vtables). El TAC no calcula direcciones; el código objeto las toma de aquí.

## 1. Orden del archivo `.tac`

Las unidades se emiten completas cuando terminan: primero `suma`, `fib`, `Cuenta`,
`Ahorro` (en el orden en que se declaran) y **al final `__main`**, que contiene todo
el código suelto del archivo.

## 2. Lectura sección por sección

### Aritmética y promoción (en `__main`)

```
let mezcla: float = total + precio * 2;
```
```
$t1 = precio * 2.0        ← el 2 se escribe 2.0: el tipo lo pide
$t2 = itof total          ← total es integer; itof lo promueve a float
$t1 = $t2 + $t1           ← $t1 se reutiliza como destino: aquí se ve el reciclaje
mezcla = $t1
```

### Lógicas con cortocircuito

```
let ok: boolean = total < LIMITE && (precio > 1.0 || total == 0);
```
```
    if total >= LIMITE goto L2     ← falso el primer operando: ya no se evalúa el resto
    if precio > 1.0 goto L1        ← verdadero el primero del ||: salta a "true"
    if total != 0 goto L2
L1: $t1 = true
    goto L3
L2: $t1 = false
L3: ok = $t1
```

La condición se compila a saltos. El booleano solo se crea (`$t1 = true/false`)
al final, porque aquí sí se guarda en una variable.

### Funciones y recursividad

```
func suma(a, b):                 func fib(n):
    $t1 = a + b                      if n >= 2 goto L7
    s = $t1                          return n
    return s                     L7: $t1 = n - 1
endfunc                              param $t1
                                     $t1 = call fib, 1
                                     $t2 = n - 2
                                     param $t2
                                     $t2 = call fib, 1
                                     $t1 = $t1 + $t2
                                     return $t1
                                 endfunc
```

* `param` por argumento, luego `call f, n` con `n` = cantidad de argumentos.
* En `fib` hay dos llamadas vivas a la vez y solo se usan `$t1` y `$t2`: el resultado
  de la primera sigue en `$t1` mientras se calcula la segunda en `$t2`.

### Clases, objetos y herencia

```
class Cuenta:
    vtable Cuenta.depositar, Cuenta.tipo       ← tabla de métodos: slot 0 y slot 1
func Cuenta.__init_fields(this):
    this.saldo = 100                            ← campos con valor inicial
func Cuenta.depositar(this, m):
    $t1 = this.saldo                            ← `saldo` sin this. se escribe this.saldo
    $t1 = $t1 + m
    this.saldo = $t1
```
```
class Ahorro : Cuenta:
    vtable Cuenta.depositar, Ahorro.tipo       ← slot 0 heredado, slot 1 sobrescrito
func Ahorro.__init_fields(this):
    param this
    call Cuenta.__init_fields, 1                ← primero los campos del padre
    this.tasa = 2
```

### Uso del objeto (en `__main`)

```
let c: Cuenta = new Ahorro();     $t1 = new Ahorro
                                  param $t1
                                  call Ahorro.__init_fields, 1
                                  c = $t1
c.saldo = 50;                     c.saldo = 50                ← almacén de campo

total = c.depositar(...)          $t2 = vtable c              ← tabla de métodos del objeto
                                  $t2 = $t2[0]                ← slot 0 = depositar
                                  param c                     ← el objeto va primero
                                  param $t1
                                  $t1 = callvirt $t2, 2       ← llamada indirecta
c.tipo()                          $t1 = vtable c
                                  $t1 = $t1[1]                ← slot 1: Ahorro.tipo, no Cuenta.tipo
                                  param c
                                  $t1 = callvirt $t1, 1
```

`c` está declarada como `Cuenta` pero apunta a un `Ahorro`: `c.tipo()` ejecuta
`Ahorro.tipo` porque el slot se lee de la tabla del objeto en tiempo de ejecución.

`x.f = y` y `x = y.f` **no** llevan offset: el TAC conserva el nombre del campo y el
offset lo da la tabla de símbolos (sección 3).

### Arreglos y control de flujo

```
$t1 = newarray 3          ← reserva
param 5
$t2 = call fib, 1
$t1[0] = $t2              ← un almacén por elemento
...
datos = $t1
```

* `while`/`for`: etiqueta de inicio, salto de salida con la condición **invertida**
  (`if i >= 3 goto L10`) y `goto` de vuelta. Así se ahorra un salto.
* `foreach`: `$t1 = len datos` y `$t2 = 0` fijan longitud e índice; el cuerpo hace
  `d = datos[$t2]`.
* `switch`: `if total == 0 goto L20 / goto L21`; los casos caen uno en el siguiente
  (no hay `break`), por eso se imprime `"cero"` y luego `"otro"`.

### try / catch

```
    try L23
    $t1 = datos[1]
    print $t1
    endtry
    goto L24
L23: catch e
    print e
L24:
```

El TAC solo marca la región protegida y el manejador (`L23`). Cómo se detecta la
excepción lo decide el código objeto.

## 3. Pestaña `symbols`: dónde vive cada cosa

### Frames (registro de activación de cada función)

```
frame = params + locals + temps*4 + 8 (fp y ra guardados)
```

| Unidad | params | locals | temps | total | Cómo sale |
|---|---|---|---|---|---|
| `__main` | 0 | 0 | 2 | 16 | `2*4 + 8`. Sus variables son globales (`gp`), no locales |
| `suma` | 8 | 4 | 1 | 24 | `a`, `b` + la local `s`; `8 + 4 + 4 + 8` |
| `fib` | 4 | 0 | 2 | 20 | `n`; los 2 temporales de la recursión |
| `Cuenta.depositar` | 8 | 0 | 1 | 20 | `this` + `m` |
| `Cuenta.tipo` / `Ahorro.tipo` | 4 | 0 | 0 | 12 | solo `this` |

Direcciones dentro del frame de `suma`: `a` = `fp+8`, `b` = `fp+12`, `s` = `fp-4`.
Parámetros hacia arriba del `fp` (los puso quien llamó), locales hacia abajo.
En un método `this` ocupa el offset 0 de los parámetros, por eso `m` queda en `fp+12`.

### Globales (`gp+offset`, fuera de cualquier frame)

| Símbolo | Dirección | Nota |
|---|---|---|
| `LIMITE` | `gp+0` | las constantes también ocupan espacio |
| `total` | `gp+4` | |
| `precio` | `gp+8` | |
| `mezcla` | `gp+12` | |
| `ok` | `gp+16` | `boolean` mide 1 byte |
| `c` | `gp+20` | una referencia, 4 bytes |
| `datos` | `gp+24` | un arreglo es una referencia |
| `i` | `gp+28` | |
| `k`, `d`, `e` | `gp+32`, `+36`, `+40` | las variables de `for`, `foreach` y `catch` en el nivel global también son globales |

### Layout de clases

```
Cuenta   size 8    this+0 = puntero a la vtable
                   saldo  @ this+4
         vtable    [0] Cuenta.depositar   [1] Cuenta.tipo

Ahorro   size 12   this+0 = puntero a la vtable
                   saldo  @ this+4        ← heredado, conserva el offset del padre
                   tasa   @ this+8        ← propio, va después
         vtable    [0] Cuenta.depositar   [1] Ahorro.tipo   ← tipo reutiliza el slot 1
```

Por eso `c.saldo` funciona igual si `c` es una `Cuenta` o un `Ahorro`: el campo está
en el mismo offset en las dos.

## 4. Qué comprobar en el IDE

1. En la pestaña `tac`, buscar `callvirt` y ver que el slot (`[0]` o `[1]`) coincide
   con la vtable de la clase.
2. En `symbols`, abrir `Ahorro` y comprobar que `saldo` sigue en `this+4`.
3. En `fib`, contar cuántos temporales distintos aparecen: solo `$t1` y `$t2`.
4. Cambiar `fib` para sumar tres llamadas (`fib(n-1) + fib(n-2) + fib(n-3)`) y ver que
   `temps` sigue en 2: la suma acumulada se queda en `$t1` y cada llamada nueva
   reutiliza `$t2`. Ese es el reciclaje.
