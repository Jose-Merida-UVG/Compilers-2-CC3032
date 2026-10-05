# Código intermedio (TAC), frames y layout

Resumen de cómo el compilador pasa de Compiscript a código intermedio y qué datos
deja listos para el código objeto (MIPS). El detalle completo está en `docs/tac.md`.
Para verlo en acción: abrir `input/comp-tac/13-recorrido-completo.cps`, **▶ Compilar**
y mirar las pestañas `tac` y `symbols`.

## 1. El flujo

```
.cps → léxico/sintaxis → semántico (tipos, tabla de símbolos) → TAC → layout
```

1. El **checker** anota cada nodo del árbol con su tipo y su símbolo.
2. El **generador de TAC** (`src/tac/`) recorre el árbol y emite instrucciones.
3. **Después** del TAC, `semantic/layout.py` recorre la tabla de símbolos y le agrega
   tamaños, offsets, direcciones y frames. Va después porque necesita saber cuántos
   temporales usó cada función.

El TAC dice *qué* hacer y en qué orden. El layout dice *dónde* vive cada dato en
memoria. El código objeto usa los dos.

## 2. El TAC

Una lista plana de instrucciones, cada una con a lo sumo tres operandos
(`x = y op z`). Las expresiones anidadas se parten en temporales:

```
let y = x * 3 + 1;          $t1 = x * 3
                            $t1 = $t1 + 1
                            y = $t1
```

### Convenciones

| Qué | Cómo |
|---|---|
| Temporales | `$t1`, `$t2`… (`$` no puede aparecer en un identificador del usuario) |
| Etiquetas | `L1`, `L2`… únicas en todo el programa; los números solo deben ser únicos |
| Variables | su nombre; si el nombre se repite en la misma función (sombreado) el segundo es `x_1` |
| Métodos | `Clase.metodo`, y reciben `this` como primer parámetro |
| Código suelto | va en `func __main():`, siempre al final |
| Formato | etiquetas y `func`/`class` pegados a la izquierda; el resto con 4 espacios |

### Instrucciones

| Instrucción | Para qué |
|---|---|
| `x = y`, `x = y OP z`, `x = - y`, `x = ! y` | copia, aritmética, lógica, unarios |
| `x = itof y` | promoción integer → float, solo cuando el tipo lo exige |
| `L:`, `goto L`, `if x goto L`, `ifFalse x goto L`, `if x REL y goto L` | saltos |
| `param x`, `x = call f, n`, `return x` | llamadas (`n` cuenta los argumentos, `this` incluido) |
| `x = newarray n`, `x[i] = y`, `x = y[i]`, `x = len y` | arreglos |
| `x = new C`, `x.f = y`, `x = y.f` | objetos y campos |
| `x = vtable y`, `x = callvirt t, n` | despacho dinámico de métodos |
| `try L` / `endtry` / `catch e` | región protegida |

Se usan las formas del libro de Aho et al. (§6.2) y se agregaron las que el lenguaje
necesita (arreglos, objetos, `vtable`, `try`).

### Cómo se traduce cada construcción

Todos los ejemplos son salida real del compilador (fuente a la izquierda, TAC a la
derecha). Cada uno tiene su demo en `input/comp-tac/`.

**Declaraciones y sombreado.** Una declaración sin valor inicial no emite nada. Si dos
variables con el mismo nombre conviven en una función, la segunda se renombra:

```
let x: integer = 1;                    x = 1
{ let x: integer = 2; print(x); }      x_1 = 2
print(x);                              print x_1
                                       print x
```

**Aritmética y promoción.** La precedencia ya viene resuelta por la gramática. Un
`integer` usado donde se pide `float` se promueve con `itof`; una constante entera se
convierte directo:

```
let r2 = a * b + c * d;                $t1 = a * b
                                       $t2 = c * d
                                       $t1 = $t1 + $t2
                                       r2 = $t1
let h = g - 1;     (g es float)        $t1 = g - 1.0
```

**Lógicas y condiciones.** Una condición se compila a saltos y `&&`/`||` hacen
cortocircuito. `!` intercambia las etiquetas de verdadero y falso. Solo si el resultado
se guarda en una variable se materializa `true`/`false`:

```
let r1 = a && b;                       ifFalse a goto L2
                                       ifFalse b goto L2
                                       $t1 = true
                                       goto L3
                                   L2:
                                       $t1 = false
                                   L3:
                                       r1 = $t1
```

**`if` / `while` / `for`.** Cada condición sabe cuál es la etiqueta que viene justo
después. Si coincide con una de sus salidas, ese salto se omite y la comparación se
**invierte** (`<` pasa a `>=`). Así el cuerpo es la caída natural y no sobra ningún
`goto`:

```
while (i < 10) {                   L1:
    s = s + i;                         if i >= 10 goto L3     ← condición invertida
    i = i + 1;                         $t1 = s + i
}                                      s = $t1
                                       $t1 = i + 1
                                       i = $t1
                                       goto L1                ← vuelta al inicio
                                   L3:
```

El `for` emite `init`, la etiqueta de inicio, la condición, el cuerpo, la etiqueta del
`update` (destino de `continue`, solo si hay alguno), el `update`, el salto de vuelta y
la etiqueta de salida (destino de `break`). Una etiqueta que ningún salto usa no se
emite.

**`foreach`.** El arreglo, su longitud y el índice se fijan en temporales que viven
hasta que termina el ciclo:

```
foreach (n in notas) { s = s + n; }

    $t1 = len notas
    $t2 = 0
L4:
    if $t2 >= $t1 goto L6
    n = notas[$t2]
    $t3 = s + n
    s = $t3
    $t2 = $t2 + 1
    goto L4
L6:
```

**`switch`.** El valor se evalúa una sola vez. Hay un `if v == c goto Lcaso` por cada
`case`, luego un salto al `default` (o al final). Cada caso termina con un `goto` al
final: los casos son excluyentes y no hace falta `break` (a diferencia de TypeScript,
porque en Compiscript `break` solo existe dentro de bucles):

```
switch (x) {                           if x == 1 goto L1
    case 1: print("uno");              if x == 2 goto L2
    case 2: print("dos");              goto L3
    default: print("otro");        L1:
}                                      print "uno"
                                       goto L4
                                   L2:
                                       print "dos"
                                       goto L4
                                   L3:
                                       print "otro"
                                   L4:
```

**`try` / `catch`.** El lenguaje no tiene `throw`, así que el TAC solo marca la región
protegida y el manejador. Si algo falla dentro (un índice fuera de rango, por ejemplo),
el control pasa a la etiqueta del `try`. Un `break`, `continue` o `return` que sale de
un `try` emite un `endtry` por cada uno que abandona:

```
try {                                  try L1
    let p = a[100];                    $t1 = a[100]
    print(p);                          p = $t1
} catch (err) {                        print p
    print(err);                        endtry
}                                      goto L2
                                   L1:
                                       catch err
                                       print err
                                   L2:
```

**Arreglos.** `[1, 2]` es `newarray` más un `t[i] = v` por elemento. Los
multidimensionales son arreglos de arreglos. Aquí el índice es el **número de
elemento** y el TAC no lo multiplica por el tamaño, a diferencia del libro (que
calcula `i * 8`). Esa multiplicación la hace el código objeto, que conoce el tamaño:

```
let a = [10, 20, 30, 40];              $t1 = newarray 4
                                       $t1[0] = 10 ...
                                       a = $t1
a[i] = a[i] + 1;                       $t1 = a[i]
                                       $t1 = $t1 + 1
                                       a[i] = $t1
```

**Funciones y llamadas.** Una llamada evalúa primero **todos** los argumentos y emite
los `param` seguidos, justo antes del `call`. Así los `param` de una llamada anidada
no se mezclan con los de la externa:

```
print(suma(doble(2), doble(3)));       param 2
                                       $t1 = call doble, 1
                                       param 3
                                       $t2 = call doble, 1
                                       param $t1
                                       param $t2
                                       $t1 = call suma, 2
                                       print $t1
```

Una llamada usada como sentencia no tiene destino (`call hola, 0`). El valor de
retorno es el destino del `call`, y el registro concreto lo decide el código objeto.
La recursividad no necesita nada especial: es una llamada normal.

### Reciclaje de temporales

Un temporal solo hace falta entre que se calcula y que se consume. Después queda libre
y el siguiente resultado puede usar el mismo nombre. Reglas (`src/tac/emitter.py`):

1. Cada función, método y `__main` tiene **su propio conjunto** de temporales.
2. `new_temp()` devuelve el **menor índice libre**, o crea uno nuevo si no hay (así la
   numeración es determinista).
3. Quien **consume** un operando lo libera (`free`) justo después de emitir la
   instrucción que lo usa, y *después* pide el temporal del resultado. Por eso
   `$t1 = $t1 + $t2` reutiliza `$t1`. Liberar una variable o una constante no hace nada.
4. Los temporales que deben vivir más (longitud e índice de un `foreach`, el valor de
   un `switch`, el objeto de un `new` hasta su llamada) se liberan al final de la
   construcción.
5. Al cerrar una unidad, si queda algún temporal vivo se lanza un error (detector de
   fugas).
6. El **pico** de temporales vivos a la vez se guarda y se convierte en `frame.temps`
   en la tabla de símbolos.

Ejemplo con `let r = (a + b) * (c + d) - (e + f) * (a + c);`:

```
CON reciclaje (3 temporales)           SIN reciclaje (7 temporales)
$t1 = a + b                            $t1 = a + b
$t2 = c + d                            $t2 = c + d
$t1 = $t1 * $t2                        $t3 = $t1 * $t2
$t2 = e + f                            $t4 = e + f
$t3 = a + c                            $t5 = a + c
$t2 = $t2 * $t3                        $t6 = $t4 * $t5
$t1 = $t1 - $t2                        $t7 = $t3 - $t6
r = $t1                                r = $t7
```

Cada resultado intermedio muere cuando la operación siguiente lo consume, así que
`$t1` y `$t2` se reutilizan. Un pico menor da un frame más pequeño (cada temporal son
4 bytes) y menos presión de registros en MIPS.

### Decisiones que conviene saber

* **Condiciones como saltos.** `if a < b && c` genera solo `if ... goto`; no se crea un
  booleano si solo se usa para saltar.
* **Campos sin offset.** Aquí se difiere del libro (§6.3): `p.y` se queda como `p.y`
  en el TAC, y el offset lo da el layout. El TAC no depende de tamaños ni de la
  arquitectura.
* **Arreglos por número de elemento**, no por bytes (ver arriba).
* **Llamadas virtuales explícitas.** `vtable` y `callvirt` no están en el libro; se
  agregaron para que un método sobrescrito se despache según el objeto real.

## 3. El layout (tabla de símbolos para el código objeto)

Cada símbolo termina con `size`, `offset`, `address` y `label`. La dirección dice
respecto a qué registro se mide:

| Dirección | Base | Qué es | Ejemplo |
|---|---|---|---|
| `gp+off` | puntero global | variables y constantes del nivel global | `total` = `gp+4` |
| `fp+off` | puntero de frame | parámetros de la función | `a` = `fp+8` |
| `fp-off` | puntero de frame | variables locales | `s` = `fp-4` |
| `this+off` | el objeto | campos de una clase | `saldo` = `this+4` |

Tamaños: `integer` y `float` 4 bytes, `boolean` 1, y todo lo demás (strings, arreglos,
objetos) son referencias de 4 bytes.

### Frame (registro de activación)

Cada función, método y `__main` recibe un frame: el bloque de pila que ocupa **una
llamada**. Cada llamada tiene el suyo, y por eso la recursión funciona (cada `fib`
tiene su propio `n`).

```
 fp+12   b            parámetros: los coloca quien llama
 fp+8    a
 fp+4    ra guardado  a dónde volver al terminar
 fp+0    fp guardado  el fp de quien llamó, para restaurarlo
 fp-4    s            locales (la primera, justo debajo del fp)
         $t1 ...      temporales, 4 bytes cada uno
```

```
total = params + locals + temps*4 + 8
```

Los 8 bytes son el `fp` y el `ra` guardados, que todas las funciones tienen. Un método
tiene al menos 12 bytes (`this` + los 8 guardados) y una función normal al menos 8.
Las variables globales no están en el frame: viven en `gp`.

Cálculo de una dirección local: `fp - (offset + tamaño)`. Para la primera local de
4 bytes, offset 0: `fp-4`.

### Clases

```
Cuenta (8 bytes)
  this+0   puntero a la vtable de la clase
  this+4   saldo
```

* La palabra 0 de todo objeto apunta a la **vtable** de su clase: una tabla con la
  dirección de cada método, una sola por clase (no una por objeto).
* Los campos van después, desde el offset 4.
* El tamaño del objeto es `4 + campos`, y es lo que `new` reserva.
* Una subclase **hereda los campos con el mismo offset** y agrega los propios después,
  así que `c.saldo` funciona igual si `c` es una `Cuenta` o un `Ahorro`.
* La vtable de la subclase copia la del padre; un método sobrescrito **reutiliza el
  slot** del ancestro.
* Una llamada a método carga la tabla del objeto y entra por el slot:

```
$t1 = vtable c        ← tabla del objeto
$t1 = $t1[1]          ← slot del método
param c               ← el objeto va primero
$t1 = callvirt $t1, 1
```

El slot se decide al compilar (según el tipo declarado) y el método que ocupa ese slot
se decide al ejecutar (según el objeto real). Eso es el despacho dinámico.

## 4. Dónde está cada cosa

| Archivo | Qué hace |
|---|---|
| `src/tac/instructions.py` | formato de las instrucciones y constantes (`$t`, `L`, `__main`) |
| `src/tac/emitter.py` | emite líneas, crea etiquetas y recicla temporales |
| `src/tac/generator.py` | el visitor principal que junta los demás |
| `src/tac/gen_core.py` | declaraciones, asignaciones, aritmética, lógicas, arreglos |
| `src/tac/gen_control.py` | `if`, ciclos, `switch`, `try/catch` |
| `src/tac/gen_functions.py` | funciones, parámetros, llamadas, recursividad |
| `src/tac/gen_classes.py` | clases, objetos, campos, herencia, vtable |
| `src/semantic/layout.py` | tamaños, offsets, direcciones, frames y layout de clases |

## 5. Qué mirar en el IDE

* Pestaña **tac**: las instrucciones de cada función; `__main` al final.
* Pestaña **symbols**: el frame de cada función (chips con los tamaños) y el layout de
  cada clase (`objeto: N B`, campos con su offset, métodos).
* Los demos `01` a `12` en `input/comp-tac/` son uno por punto de la rúbrica, con su
  versión inválida; el `13` junta todo.
