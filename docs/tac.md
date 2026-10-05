# Código intermedio (Proyecto 2)

Especificación del código de tres direcciones (TAC) que genera el compilador:
formato, decisiones de diseño, traducción por construcción, reciclaje de
temporales, tabla de símbolos para el código objeto y organización de `src/tac/`.
Los ejemplos de TAC y los JSON de la tabla de símbolos son salida real del
generador para los casos de `src/tests/tac/<área>/valido_*.cps` (y los
`valido_*.symbols.json` de `tabla_simbolos/`); en los fragmentos se omiten líneas con `...` y la
fuente se acomodó en columnas junto al TAC).

Contexto: [`semantic.md`](semantic.md) (análisis previo) y
[`ARCHITECTURE.md`](ARCHITECTURE.md) (pipeline completo).

> **Alcance.** El compilador solo *genera* TAC como **texto**: no lo ejecuta ni
> produce código objeto, y si el programa tiene cualquier error (léxico,
> sintáctico o semántico) no se genera TAC.
>
> **Representación.** El libro (Aho et al., §6.2.2–6.2.3) define el TAC como
> estructuras de datos: cuádruplas `(op, arg1, arg2, resultado)` o triplas. Aquí
> **no se construyen**: cada instrucción es una línea de texto que el `Emitter`
> agrega a una lista, porque lo que se entrega y se muestra es el texto (IDE y
> archivo `.tac`). El formato es regular (§4), así que cada línea se descompone en
> operador y operandos, pero la fase de MIPS tendrá que parsear el texto o
> introducir cuádruplas. La tabla de símbolos sí guarda lo que esa fase
> necesita: tamaños, direcciones y registros de activación (§9).

## 1. Formato

Una lista plana de instrucciones, cada una con a lo sumo **tres operandos**
(`x = y OP z`). Las expresiones anidadas y el control de flujo se descomponen en
temporales, etiquetas y saltos:

```
let y = x * 3 + 1;          $t1 = x * 3
                            $t1 = $t1 + 1
                            y = $t1
```

## 2. Decisiones de diseño

| Decisión | Elegido | Justificación |
|---|---|---|
| Sintaxis | Estilo *Dragon Book*: `x = y op z`, `goto L`, `if x goto L`, `ifFalse x goto L`, `param`/`call`/`return`, `x[i]` | Repertorio estándar; una línea por instrucción. |
| Representación | Texto: una línea por instrucción, una lista de líneas por función (sin cuádruplas ni triplas, ver arriba) | El entregable es el texto; el formato regular permite descomponer cada línea si una fase posterior lo necesita. |
| Temporales | `$t1`, `$t2`… | `$` no puede aparecer en un identificador del usuario. |
| Etiquetas | `L1`, `L2`… únicas en todo el programa | Numeración creciente, sin reiniciar por función. |
| Condiciones | Saltos directos (`if a < b goto L`); no se materializa un booleano si solo se usa para saltar | Menos instrucciones y temporales; `&&`/`||` con cortocircuito real. |
| Top-level | Código suelto en `func __main():`, emitido al final | Un único punto de entrada; funciones y clases quedan definidas antes. |
| Llamadas | `param` por argumento y `call f, n` | Se traduce directo a una pila de argumentos en MIPS. |
| Clases | Métodos como funciones con `this` primero; etiqueta `Clase.metodo`. Cada clase declara una tabla de métodos (`vtable`) y las llamadas a método son indirectas (`callvirt`) | Un método sobrescrito se despacha según la clase real del objeto, no la del tipo estático (§6.12). |
| Campos y memoria | `x.f = y`, `x = y.f`, sin aritmética de direcciones | Se desvía del libro (§6.3), que calcula `base + offset` en el TAC. Aquí el TAC conserva el nombre del campo y el offset lo resuelve el código objeto con el layout de la tabla de símbolos (§9). Evita que el TAC dependa de tamaños y de la arquitectura, y deja el cálculo de offsets (herencia incluida) en un solo lugar. |

## 3. Operandos y nombres

Un operando es siempre texto:

| Operando | Ejemplos | Notas |
|---|---|---|
| Variable | `x`, `suma`, `x_1` | Si dos símbolos con el mismo nombre conviven en una función (sombreado en bloques), el segundo se llama `x_1`, el tercero `x_2`… Parámetros y campos conservan su nombre. |
| Temporal | `$t1`, `$t2` | Se reciclan (§8). |
| Constante | `5`, `3.14`, `"hola"`, `true`, `false`, `null` | Un entero usado donde se espera `float` se convierte en el acto (`5` → `5.0`). |
| Etiqueta | `L1` | Solo en `goto`, saltos condicionales y `try`. |
| `this` | `this` | Primer parámetro de todo método. |

Nombres de unidades: funciones `f`, métodos `Clase.metodo`, constructor
`Clase.constructor`, inicializador de campos `Clase.__init_fields`.

## 4. Instrucciones

| Instrucción | Significado |
|---|---|
| `x = y` | copia |
| `x = y OP z` | `OP` ∈ `+ - * / % == != < <= > >=` (con strings, `+` concatena) |
| `x = - y`, `x = ! y` | unarios |
| `x = itof y` | promoción integer → float (solo cuando el tipo lo exige) |
| `L:` | etiqueta |
| `goto L` | salto incondicional |
| `if x goto L`, `if x REL y goto L` | salto si verdadero |
| `ifFalse x goto L` | salto si falso |
| `param x` | argumento (en orden, justo antes del `call`) |
| `x = call f, n`, `call f, n` | llamada con `n` argumentos (cuenta `this`); sin destino si el valor no se usa |
| `return x`, `return` | retorno |
| `x = newarray n` | arreglo de `n` elementos |
| `x[i] = y`, `x = y[i]`, `x = len y` | arreglos |
| `x = new C` | reserva una instancia de `C` y guarda en su primera palabra (`this+0`) la tabla de métodos de `C` |
| `x.f = y`, `x = y.f` | campos |
| `vtable M1, M2, …` | dentro de `class`: la tabla de métodos de la clase, un slot por etiqueta (el slot 0 es `M1`) |
| `x = vtable y` | carga en `x` la tabla de métodos del objeto `y` |
| `x = callvirt t, n`, `callvirt t, n` | llamada indirecta: `t` contiene la dirección del método (una entrada de la tabla); `n` cuenta `this` |
| `print x` | `print(...)` del lenguaje |
| `try L` / `endtry` / `catch e` | región protegida (§6.8) |
| `func f(p1, p2):` … `endfunc` | función; métodos: `func Clase.m(this, p1):` |
| `class C : P:` … `endclass` | agrupa los métodos de una clase (`: P` solo si hereda) |

Formato: etiquetas y `func`/`endfunc`/`class`/`endclass` pegados a la izquierda;
el resto de instrucciones con 4 espacios de sangría (indentación).

**Relación con el libro** (Aho et al., 2.ª ed., §6.2.1). Se usan las formas 1 a 8
del libro: asignación binaria y unaria (incluida la conversión de tipo), copia,
`goto`, `if x goto`, `ifFalse x goto`, `if x relop y goto`, `param`/`call p, n`/
`y = call p, n`/`return y` y la copia indexada. Como en el libro, `n` en `call`
no es redundante y se conserva. Las formas de dirección y puntero (`&`, `*`) no se
usan. Lo que **no está en el libro** y se agregó porque el lenguaje lo necesita:

| Extensión | Motivo |
|---|---|
| `newarray n`, `len y` | crear un arreglo y conocer su tamaño (`foreach`) |
| `vtable`, `x = vtable y`, `callvirt` | despacho dinámico de métodos; el libro habla de llamadas virtuales como llamadas indirectas (§12.2.1) pero no define una instrucción ni una tabla de métodos |
| `new C`, `x.f` | instancias y campos; el libro los resuelve con direcciones base + desplazamiento (§6.3), aquí se deja al código objeto con el layout de la tabla de símbolos (ver §6.11) |
| `print x` | `print(...)` del lenguaje |
| `try L` / `endtry` / `catch e` | región protegida |
| `func`/`endfunc`, `class`/`endclass` | agrupar el código por unidad |

Dos diferencias de notación: la conversión se escribe `itof` y el menos unario
`- y` (el libro usa `minus`), y los temporales llevan `$` (`$t1`).

## 5. Estructura de un programa

Las unidades (`func`, `class`) se emiten completas cuando terminan; las
anidadas salen después de su contenedora; `__main` siempre al final. Toda
función termina en `return` si su cuerpo puede acabar sin pasar por uno (así
ninguna etiqueta queda al final sin código).

```
func fact(n):
    if n > 1 goto L2
    return 1
L2:
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

## 6. Traducción por construcción

### 6.1 Declaraciones y asignación

Una declaración sin inicializador no emite nada (el TAC no inicializa por
defecto). Se respeta el sombreado:

```
let x: integer = 1;                    x = 1
{ let x: integer = 2; print(x); }      x_1 = 2
print(x);                              print x_1
                                       print x
```

### 6.2 Aritmética y promoción

La precedencia la da la gramática. Cada operando se libera apenas se consume,
así que el resultado reutiliza el temporal (ver §8):

```
let r2 = a * b + c * d;                $t1 = a * b
                                       $t2 = c * d
                                       $t1 = $t1 + $t2
                                       r2 = $t1
```

`integer` mezclado con `float` se promueve con `itof`; las constantes enteras se
convierten directamente:

```
let a = i + f;                         $t1 = itof i
let c = f - 1;                         $t1 = $t1 + f
                                       a = $t1
                                       $t1 = f - 1.0
                                       c = $t1
```

### 6.3 Condiciones y lógicas

Las condiciones son saltos. `&&` y `||` hacen cortocircuito; `!` intercambia
las etiquetas. Como *valor* (`let r = a && b;`) se materializa `true`/`false`:

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

El ternario `c ? x : y` usa las mismas etiquetas y deja ambas ramas en el mismo
temporal.

### 6.4 Arreglos

`[1, 2]` → `newarray` y un `t[i] = v` por elemento; `a[i]` es copia indexada;
`len` lo usa `foreach`. Los multidimensionales son arreglos de arreglos.

**Diferencia con el libro:** en `x = y[i]` del libro, `i` son *unidades de
memoria* (el ejemplo 6.5 calcula `t2 = i * 8` y luego `a[t2]`). Aquí `i` es el
**número de elemento**: el TAC no multiplica por el tamaño, lo hará el código
objeto con el tamaño del elemento (§9).

```
let a = [10, 20, 30, 40];              $t1 = newarray 4
                                       $t1[0] = 10
                                       ...
                                       a = $t1
let q = a[i + 1];                      $t1 = i + 1
                                       $t1 = a[$t1]
                                       q = $t1
a[i] = a[i] + 1;                       $t1 = a[i]
                                       $t1 = $t1 + 1
                                       a[i] = $t1
```

### 6.5 if / while / do-while / for

Cada condición se compila con `gen_cond(cond, ltrue, lfalse, fall)`, donde
`fall` es la etiqueta que se coloca justo después. Si coincide con una de las
dos salidas, ese salto se omite y la condición se **invierte** (`<` pasa a
`>=`): el cuerpo es la caída natural y no sobra ningún `goto`. Una etiqueta que
ningún salto referencia no se emite.

**`if` / `else`.** Sin `else`, la salida falsa va directo al final. Con `else`, el
bloque `then` termina con un `goto` al final (salvo que ya acabe en
`return`/`break`/`continue`). `else if` es un `if` anidado. Una condición con
`&&`/`||` encadena saltos sin construir un booleano:

```
if (x < 10) {                          if x >= 10 goto L2
    print("chico");                    print "chico"
} else {                               goto L3
    if (x < 20) {                  L2:
        print("mediano");              if x >= 20 goto L5
    } else {                           print "mediano"
        print("grande");               goto L6
    }                              L5:
}                                      print "grande"
                                   L6:
                                   L3:
if (a < b && b < 10) {                 if a >= b goto L8
    print("rango");                    if b >= 10 goto L8
}                                      print "rango"
                                   L8:
```

**`while`.** Etiqueta de condición, cuerpo y salto de vuelta:

```
while (i < 10) {                   L1:
    suma = suma + i;                   if i >= 10 goto L3
    i = i + 1;                         $t1 = suma + i
}                                      suma = $t1
                                       $t1 = i + 1
                                       i = $t1
                                       goto L1
                                   L3:
```

**`do-while`.** El cuerpo va primero; la condición está al final y salta de
vuelta al inicio cuando es verdadera (la caída es la salida). `continue` salta
a la etiqueta de la condición, que solo se emite si hay algún `continue`:

```
do {                               L1:
    n = n - 1;                         $t1 = n - 1
    if (n == 5) { continue; }          n = $t1
    print(n);                          if n != 5 goto L5
} while (n > 0);                       goto L2
                                   L5:
                                       print n
                                   L2:
                                       if n > 0 goto L1
```

**`for`.** Se emite `init`, la etiqueta de inicio, la condición, el cuerpo, la
etiqueta de `update` (destino de `continue`, solo si hay alguno), el `update`,
el salto de vuelta y la etiqueta de salida (destino de `break`). `init`, `cond`
y `update` son opcionales (`for (;;)` es un ciclo sin condición):

```
for (let i: integer = 0;           i = 0
     i < 5; i = i + 1) {       L1:
    if (i == 3) { continue; }      if i >= 5 goto L4
    if (i > 6) { break; }          if i != 3 goto L6
    total = total + i;             goto L3
}                              L6:
                                   if i <= 6 goto L8
                                   goto L4
                               L8:
                                   $t1 = total + i
                                   total = $t1
                               L3:
                                   $t1 = i + 1
                                   i = $t1
                                   goto L1
                               L4:
```

`continue` salta a `L3` (el `update`) y `break` a `L4` (la salida).

### 6.6 foreach

El arreglo, su longitud y el índice son temporales **fijados** que se liberan
al terminar el ciclo:

```
foreach (n in notas) { suma = suma + n; }

    $t1 = len notas
    $t2 = 0
L1:
    if $t2 >= $t1 goto L3
    n = notas[$t2]
    $t3 = suma + n
    suma = $t3
    $t2 = $t2 + 1
    goto L1
L3:
```

### 6.7 switch y break/continue

El valor del `switch` se evalúa **una sola vez** (queda en un temporal fijado
que se libera antes de generar los cuerpos). Hay un `if v == c goto Lcase` por
cada `case`, y después `goto Ldefault` (o `goto Lend` si no hay `default`). Los
cuerpos van en orden y **cada caso cae en el siguiente**: no existe un `break`
implícito ni una salida propia del `switch` (el ejemplo de
`docs/enunciados/DefinicionCompiscript.md` imprime "uno", "dos" y "otro" para `x = 1`).

```
switch (x) {                           if x == 1 goto L1
    case 1: print("uno");              if x == 2 goto L2
    case 2: print("dos");              goto L3
    default: print("otro");        L1:
}                                      print "uno"
                                   L2:
                                       print "dos"
                                   L3:
                                       print "otro"
```

**`break` y `continue` pertenecen solo a los bucles.** La especificación del
proyecto los limita a bucles (el analizador semántico rechaza un `break` fuera
de uno), así que el `switch` **no apila etiquetas**: dentro de un `switch` que
está en un `while`, `for`, `do-while` o `foreach`, `break` y `continue` se
refieren a ese bucle, no al `switch`. Cada bucle apila su par
(`break` → etiqueta de salida, `continue` → etiqueta de continuación) mientras
genera el cuerpo y lo desapila al terminar; `break`/`continue` son un `goto` al
tope de esa pila.

```
while (i < 6) {                    L1:
    switch (i % 3) {                   if i >= 6 goto L3
        case 0:                        $t1 = i % 3
            i = i + 1;                 if $t1 == 0 goto L4
            continue;                  if $t1 == 1 goto L5
        case 1:                        goto L6
            if (i > 3) { break; }  L4:
        default:                       $t1 = i + 1
            print(i);                  i = $t1
    }                                  goto L1       ← continue: al while
    i = i + 1;                     L5:
}                                      if i <= 3 goto L9
                                       goto L3       ← break: sale del while
                                   L9:
                                   L6:
                                       print i
                                       $t1 = i + 1
                                       i = $t1
                                       goto L1
                                   L3:
```

### 6.8 try / catch

El lenguaje no tiene `throw`; el TAC marca la región protegida y el manejador.
Si ocurre una excepción dentro de la región (por ejemplo un índice fuera de
rango), el control pasa a la etiqueta del `try`:

```
try {                                  try L1
    let peligro = a[100];              $t1 = a[100]
    print(peligro);                    peligro = $t1
} catch (err) {                        print peligro
    print("Error atrapado: " + err);   endtry
}                                      goto L2
                                   L1:
                                       catch err
                                       $t1 = "Error atrapado: " + err
                                       print $t1
                                   L2:
```

`break`, `continue` y `return` que salen de un `try` emiten un `endtry` por cada
`try` abierto antes de saltar (el valor de un `return` se calcula dentro del
`try` y luego se sale de él):

```
function primero(a: integer[]): integer {   func primero(a):
    try { return a[0]; }                        try L1
    catch (e) { print(e); }                     $t1 = a[0]
    return 0;                                   endtry
}                                               return $t1
                                            L1:
                                                catch e
                                                print e
                                                return 0
                                            endfunc
```

### 6.9 Funciones, parámetros y llamadas

Una función es una unidad con su propio conjunto de temporales. Una llamada
`f(e1, e2)` **evalúa primero todos los argumentos** y luego emite los `param`
seguidos, justo antes del `call`; así los `param` de una llamada anidada no se
intercalan con los de la externa. Cada temporal se libera justo después de su
`param`, y el resultado reutiliza el temporal de su argumento:

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

Una llamada usada como sentencia, o de una función `void`, no tiene destino
(`call hola, 0`). Un argumento entero que va a un parámetro `float` se promueve
(`param 1.0`). Las funciones anidadas se emiten después de la contenedora y se
llaman por su nombre.

### 6.10 Recursividad

Es una llamada normal: el símbolo de la función ya existe cuando se genera su
cuerpo. Los temporales se reciclan entre llamadas anidadas:

```
function fib(n: integer): integer {    func fib(n):
    if (n < 2) { return n; }               if n >= 2 goto L2
    else { return fib(n-1) + fib(n-2); }   return n
}                                      L2:
                                           $t1 = n - 1
                                           param $t1
                                           $t1 = call fib, 1
                                           $t2 = n - 2
                                           param $t2
                                           $t2 = call fib, 1
                                           $t1 = $t1 + $t2
                                           return $t1
                                       endfunc
```

### 6.11 Clases y objetos

Cada clase es una unidad `class … endclass` que contiene un `__init_fields`
sintetizado y sus métodos. `__init_fields(this)` llama al del padre (si hay) y
asigna los campos que tienen valor inicial. Los métodos reciben `this` primero.

```
class Punto {                          class Punto:
    var x: integer = 0;                func Punto.__init_fields(this):
    var y: integer = 0;                    this.x = 0
    function constructor(a, b) {           this.y = 0
        this.x = a; this.y = b;            return
    }                                  endfunc
}                                      func Punto.constructor(this, a, b):
                                           this.x = a
                                           this.y = b
                                           return
                                       endfunc
                                       endclass
```

`new` reserva, evalúa los argumentos, inicializa los campos y llama al
constructor (si lo hay). El objeto es un temporal que vive hasta terminar las
llamadas y es el resultado de la expresión:

```
let p = new Punto(3, 4);               $t1 = new Punto
                                       param $t1
                                       call Punto.__init_fields, 1
                                       param $t1
                                       param 3
                                       param 4
                                       call Punto.constructor, 3
                                       p = $t1
```

Acceso y asignación de campos, y llamada a un método. El objeto va como primer
`param` y el método se busca por su slot en la tabla del objeto (§6.12):

```
print(p.x);                            $t1 = p.x
p.y = p.x + 1;                         print $t1
                                       $t1 = p.x
                                       $t1 = $t1 + 1
                                       p.y = $t1
c.sumar(10)                            $t1 = vtable c
                                       $t1 = $t1[0]
                                       param c
                                       param 10
                                       $t1 = callvirt $t1, 2
```

El TAC no calcula direcciones de campos: `p.y` se queda como `p.y` y el código
objeto lo convierte en `lw`/`sw offset(reg)` con el offset de `layout.py` (§9). El
libro lo haría en el TAC con `t = p + 8` y `*t`; aquí se difiere a propósito (§2).

Las cadenas se evalúan de izquierda a derecha con un operando "base":
`a.siguiente.valor = 5;` →

```
    $t1 = a.siguiente
    $t1.valor = 5
```

### 6.12 Herencia y despacho dinámico

Los campos heredados conservan su offset (§9) y `__init_fields` de la subclase
llama primero al del padre.

**Tabla de métodos.** Cada clase con métodos declara su tabla con una línea
`vtable` al inicio de su unidad. Los slots del padre van primero y un método
sobrescrito reutiliza el slot del ancestro, así que un mismo método tiene el mismo
número de slot en toda la jerarquía. Los constructores y `__init_fields` no
entran en la tabla: se llaman por su etiqueta (`call`).

**Llamada a un método.** Se carga la tabla del objeto, se toma la entrada del slot
(el slot sale del tipo estático) y se llama de forma indirecta. Como la tabla es
la de la clase *real* del objeto, una variable de tipo `A` que guarda una `C`
llama al método de `C`. Lo mismo vale para `this.m()` (o `m()`) dentro de un
método de la clase padre.

```
class A { var a: integer = 1; function quien() {…} function soloA() {…} }
class B : A { var b: integer = 2; function quien() {…} }
class C : B { var c: integer = 3; … }

class C : B:
    vtable B.quien, A.soloA            slot 0 = quien (de B), slot 1 = soloA (de A)
func C.__init_fields(this):
    param this
    call B.__init_fields, 1
    this.c = 3
    return
endfunc

let x: A = new C();                    $t1 = new C                 (guarda la tabla de C)
                                       …
                                       x = $t1
x.quien()                              $t1 = vtable x
                                       $t1 = $t1[0]                (slot de quien)
                                       param x
                                       $t1 = callvirt $t1, 1
x.soloA()                              $t1 = vtable x
                                       $t1 = $t1[1]                (slot de soloA)
                                       param x
                                       $t1 = callvirt $t1, 1
```

Si ni la clase ni sus ancestros declaran `constructor`, `new` solo llama a
`__init_fields`. Si lo declara un ancestro, se llama a ese (`Animal.constructor`).

## 7. Convención de llamada (relación con MIPS)

* El llamador emite `param` en orden y luego `call f, n`; `n` incluye a `this`.
* El valor de retorno es el destino de `call` (`$t = call …`); el llamado lo
  entrega con `return x`. La fase de código objeto decidirá el registro.
* En el registro de activación (§9) los parámetros están sobre el `ra` y el
  `fp` guardados; el primer parámetro es el de menor dirección.

## 8. Reciclaje de temporales

Un temporal solo hace falta entre el momento en que se calcula y el momento en
que se consume. Después queda libre y el siguiente resultado puede ocupar el
mismo nombre. El libro (§6.2.1) crea un nombre distinto por cada temporal y deja
combinarlos para cuando se asignen registros; aquí el reciclaje se hace al
generar. El algoritmo (implementado en `src/tac/emitter.py`):

1. Cada función (y cada método) tiene su **propio pool** de temporales; se
   reinicia al abrir la unidad.
2. `new_temp()` devuelve el **menor índice libre**, o crea uno nuevo si no hay
   (así la numeración es determinista).
3. Quien **consume** un operando lo libera (`free`) justo después de emitir la
   instrucción que lo usa, y *después* pide el temporal del resultado. Por eso
   `$t1 = $t1 + $t2` reutiliza `$t1`. `free` de una variable o constante no
   hace nada.
4. Los temporales que deben vivir más (longitud e índice de un `foreach`, el
   valor de un `switch`, el objeto de un `new` hasta su llamada) se liberan
   explícitamente al final de la construcción.
5. Al cerrar una unidad, si quedó algún temporal vivo se lanza un error
   (detector de fugas); las pruebas lo ejercitan en cada caso.
6. El **pico** de temporales simultáneos de cada unidad se guarda y alimenta
   `frame.temps` en la tabla de símbolos.

### 8.1 Pseudocódigo

Estado de cada unidad (función, método o `__main`):

```
libres    ← min-heap vacío        # índices que ya se pueden reutilizar
vivos     ← conjunto vacío        # índices en uso ahora
siguiente ← 0                     # mayor índice creado hasta el momento
pico      ← 0                     # máximo de temporales vivos a la vez
```

Operaciones del emisor:

```
new_temp():
    si libres no está vacío:
        i ← extraer_mínimo(libres)        # reutiliza el menor índice libre
    si no:
        siguiente ← siguiente + 1         # solo crea uno nuevo si no hay libres
        i ← siguiente
    vivos ← vivos ∪ {i}
    pico  ← máx(pico, |vivos|)
    devolver "$t" + i

free(operando):
    si operando no tiene la forma "$t<i>":
        devolver                          # variable o constante: nada que liberar
    si i ∈ vivos:
        vivos ← vivos \ {i}
        insertar(libres, i)

end_unit():
    si vivos no está vacío:  error "fuga de temporales"
    max_temps[nombre de la unidad] ← pico
```

Cómo lo usa cada generador de expresiones (la regla clave es **liberar los
operandos antes de pedir el temporal del resultado**):

```
gen_binaria(a OP b):
    ta ← gen(a)                           # operando izquierdo (variable, constante o $t)
    tb ← gen(b)
    free(ta); free(tb)                    # 1) se liberan los operandos…
    t  ← new_temp()                       # 2) …y el resultado puede ocupar ta o tb
    emitir(t = ta OP tb)
    devolver t
```

### 8.2 Ejemplo comparativo: con y sin reciclaje

Fuente: `let r = (a + b) * (c + d) - (e + f) * (a + c);`

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

Cada resultado intermedio muere en cuanto la operación siguiente lo consume,
así que `$t1` y `$t2` se reutilizan y solo `$t3` hace falta para la última
suma. Sin reciclaje cada resultado estrena un temporal nuevo y el total crece
con el tamaño de la expresión. En una suma encadenada la diferencia es aún
mayor (`let s = a + b + c + d + e + f;`):

```
CON reciclaje (1 temporal)             SIN reciclaje (5 temporales)
$t1 = a + b                            $t1 = a + b
$t1 = $t1 + c                          $t2 = $t1 + c
$t1 = $t1 + d                          $t3 = $t2 + d
$t1 = $t1 + e                          $t4 = $t3 + e
$t1 = $t1 + f                          $t5 = $t4 + f
s = $t1                                s = $t5
```

La columna "sin reciclaje" es salida real del generador con `free()`
desactivado en el emisor. El número de temporales importa más adelante: el pico
de cada función es `frame.temps` en la tabla de símbolos (§9), y cada temporal
ocupa 4 bytes en su registro de activación. Un pico menor da un `frame` más
pequeño y menos presión de registros en MIPS.

## 9. Tabla de símbolos para el código objeto

Tras generar el TAC, `semantic/layout.py` recorre el árbol de ámbitos y completa
cada símbolo con `size`, `offset`, `address` y `label`; cada ámbito de función
con su registro de activación (`frame`) y cada ámbito de clase con su `layout`.
Aparece en el JSON del panel **symbols** y en `<archivo>.symbols`.

Esto es lo que el TAC deja sin resolver a propósito: los offsets de campos, las
direcciones de variables y parámetros y la posición de la tabla de métodos se
toman de aquí al generar el código objeto.

**Tamaños (MIPS32):** `integer` 4, `float` 4, `boolean` 1; `string`, arreglo,
instancia, función y `null` son referencias de 4 bytes. Alineación natural y
cada área redondeada a múltiplo de 4.

**Direcciones:** globales `gp+off`; parámetros `fp+8+off`; locales
`fp-(off+tamaño)`; campos `this+off`. Un método reserva el offset 0 de sus
parámetros para `this`.

**Objetos:** la primera palabra de toda instancia (`this+0`) guarda el puntero a la
tabla de métodos de su clase, así que los campos empiezan en el offset 4 y una
clase sin campos mide 4 bytes. Cada método del `layout` trae su `slot` y la clase
trae su `vtable`.

```
        parámetros (los empuja el llamador)     fp+8 …
        ra guardado                             fp+4
        fp guardado                             fp+0
        locales                                 fp-4, fp-8 …
        temporales (4 bytes c/u)
```

`__main` (el código de nivel superior) también tiene su `frame`, que cuelga del
ámbito global: `params_size` y `locals_size` valen 0 porque sus variables son
globales (`gp`); solo guarda temporales y `ra`/`fp`. Cada símbolo trae además
`tac_name`, el nombre con el que aparece en el TAC (`x_1` si hubo sombreado), de
modo que todo nombre del TAC se puede enlazar con su símbolo.

`frame.total_size = params_size + locals_size + temps_size + saved_size`
(`saved_size` = 8: `ra` y `fp`). Ejemplo, el método `depositar(monto)` de una
clase con una local y un temporal:

```json
"frame": { "label": "Cuenta.depositar", "params_size": 8, "locals_size": 4,
           "temps": 1, "temps_size": 4, "saved_size": 8, "total_size": 24 }
```

Layout de clase: los campos heredados van primero, en los mismos offsets que en
el padre; los métodos indican qué etiqueta del ancestro sobrescriben (un
constructor nunca se reporta como sobrescritura):

```json
"layout": { "size": 20, "parent": "Animal",
  "fields": [ {"name":"nombre","offset":4,"size":4,"inherited":true},
              {"name":"patas","offset":8,"size":4,"inherited":true},
              {"name":"vivo","offset":12,"size":1,"inherited":false},
              {"name":"raza","offset":16,"size":4,"inherited":false} ],
  "methods": [ {"name":"hablar","label":"Perro.hablar","slot":0,"overrides":"Animal.hablar"} ],
  "vtable":  [ {"slot":0,"name":"hablar","label":"Perro.hablar"} ] }
```

## 10. El generador por dentro (`src/tac/`)

**Dónde encaja.** `compiler.analyze()` corre el `TACGenerator` sobre el mismo
árbol, **solo si el checker terminó con cero errores**, y después
`layout.assign_layout()` con los picos de temporales del emisor. Una excepción
del generador se reporta como error interno en vez de tumbar el IDE, y en ese
caso tampoco hay TAC.

**Organización.** `TACGenerator(CoreMixin, ControlMixin, FunctionMixin,
ClassMixin, CompiscriptVisitor)`: cada regla de la gramática la implementa **un
solo** mixin, así que no se pisan. Las expresiones devuelven un *operando*
(variable, temporal `$tN` o constante); quien lo consume lo libera con `free`
justo después de emitir la instrucción que lo usa.

| Archivo | Rol |
|---|---|
| `instructions.py` | Convenciones de formato: sangría, prefijos `$t` y `L`, nombre `__main`, cabeceras de `func`/`class`, instrucciones `call` y `callvirt`. |
| `emitter.py` | `Emitter`: emite líneas, etiquetas únicas, pool de temporales por unidad (§8), pila de unidades, detector de fugas y `max_temps`. Renderiza las funciones primero y `__main` al final. |
| `generator.py` | `TACGenerator`: une los mixins y ofrece `expr`, `type_of`, `symbol_of`, `scope_of`, `name_of` (nombres únicos por unidad: `x`, `x_1`…). |
| `gen_core.py` | `CoreMixin`: declaraciones, asignaciones, aritmética (con `itof`), comparaciones, `&&`/`\|\|` con cortocircuito, ternario, arreglos, `print` y `gen_cond`. |
| `gen_control.py` | `ControlMixin`: `if`/`else`, `while`, `do-while`, `for`, `foreach`, `switch`, `break`/`continue`, `try`/`catch`. |
| `gen_functions.py` | `FunctionMixin`: funciones, parámetros, `return`, llamadas (`param`/`call`) y recursividad. |
| `gen_classes.py` | `ClassMixin`: clases (línea `vtable` y `__init_fields` sintetizado), `new`, `this`, acceso a campos, la cadena de sufijos `leftHandSide` (`eval_chain`, que decide el slot de cada llamada a método) y herencia. |

**Anotaciones del checker.** El generador no vuelve a inferir tipos ni resolver
nombres: reutiliza `node_types`, `node_symbols`, `node_scopes` y
`node_inner_scopes` que guardó el `SemanticChecker` por `id(ctx)`.
`name_of(symbol)` resuelve el sombreado con nombres únicos por unidad.

**Condiciones: `gen_cond(cond, ltrue, lfalse, fall)`.** Toda condición (de `if`,
bucles, ternario, `&&`/`||` y `!`) pasa por aquí. Desciende la cadena de
precedencia hasta el operador real y emite saltos directos, sin construir un
booleano; `&&`/`||` encadenan etiquetas intermedias y `!` las intercambia.
`fall` es la etiqueta que se colocará justo después: si coincide con una de las
salidas se omite ese `goto` invirtiendo el operador relacional (§6.5).

**Contratos entre mixins.** Quien necesita evaluar una expresión llama
`self.expr(ctx)`, y quien necesita saltar según una condición llama `gen_cond`;
nunca se reimplementa lo del otro. Los arreglos se reparten así: `CoreMixin`
expone `gen_index_load`/`gen_index_store`, y `ClassMixin` expone
`eval_chain(ctx, n)`, que `CoreMixin` usa en asignaciones como `a.b[i] = v`.
`ControlMixin` lleva la cuenta de `try` abiertos (`open_tries`), y un `return`
dentro de un `try` emite un `endtry` por cada uno.

**IDE.** `/api/run` devuelve `tac` y `tacStats` (`instructions`, `temps`,
`functions`), `None` ambos si hubo algún error. El visor **Código intermedio
(TAC)** muestra numeración de líneas, resaltado de etiquetas, saltos,
temporales y `func`/`endfunc`, y un botón para copiar; con errores no se abre y
avisa que no se generó código. La **Tabla de símbolos** muestra además tamaño,
offset y dirección de cada símbolo, el registro de activación de cada función y
el layout de cada clase.

## 11. Supuestos y limitaciones

* **Despacho dinámico solo para métodos.** Las llamadas a método van por la tabla
  del objeto (§6.12). El constructor y `__init_fields` se resuelven por la clase
  nombrada, y no se valida que una sobrescritura tenga la misma firma (limitación
  del checker, ver [`semantic.md`](semantic.md) §9).
* **Cierres:** una función anidada que usa variables de la contenedora las
  nombra tal cual; el TAC no modela el entorno capturado.
* `try/catch`: el lenguaje no tiene `throw`; el TAC solo marca la región y el
  manejador, y la fase de código objeto decide cómo detectar la excepción.
* `break`/`continue` solo existen dentro de bucles (restricción del enunciado), así
  que un `switch` no se puede abandonar con `break`: cada caso cae en el siguiente.
* Una variable declarada sin inicializador no genera instrucción.

## 12. Cómo producirlo y probarlo

* IDE: `make run` y **▶ Compilar** sobre un `.cps`; las vistas **Código
  intermedio (TAC)** y **Tabla de símbolos** muestran el resultado y se guarda
  `workspace/output/<nombre>/<nombre>.cps.tac`.
* CLI: `make cli FILE=workspace/input/comp-tac/06-funciones-valido.cps`.
* Casos de demostración: `workspace/input/comp-tac/` (un `NN-<área>-valido.cps` y un
  `NN-<área>-invalido.cps` por cada fila de la rúbrica, numerados en su orden, más
  `13-recorrido-completo.cps` con todas las áreas juntas).

**Pruebas.** `src/tests/tac/<área>/` tiene una carpeta por punto de la rúbrica,
con `valido_<caso>.cps` (debe compilar y generar TAC) e `invalido_<caso>.cps`
(debe dar errores y **ningún** TAC). Además:

| Archivo | Qué comprueba |
|---|---|
| `test_tac_casos.py` | todos los casos por `analyze()`, el camino real |
| `test_tac_tono.py` | funciones, recursividad, clases, herencia y tabla de símbolos por `compile_tac`; asignación a propiedad como expresión; resolución estática de métodos (§11) |
| `test_tac_invariantes.py` | propiedades de todo TAC válido: `param` antes de cada `call`, aridad, etiquetas definidas y usadas, `return` final, pico de temporales, sin fugas |
| `test_cobertura_rubrica.py` | cada fila de la rúbrica tiene área, ≥3 casos válidos, ≥2 inválidos, las construcciones que nombra y demos |
| `tabla_simbolos/` | JSON esperado de la tabla de símbolos (`valido_*.symbols.json`) y reglas de layout |
| `temporales/` | emisor, reciclaje y compilación |

Los `valido_*.symbols.json` se regeneran con
`UPDATE_GOLDEN=1 make test ARGS="src/tests/tac/tabla_simbolos"`; revisar el diff
a mano. `make test` corre la suite completa (466 pruebas).

## 13. Cómo se implementa cada punto de la rúbrica

| Punto (pts) | Cómo funciona | Código | Pruebas |
|---|---|---|---|
| Diseño del código intermedio (3) | TAC estilo *Dragon Book*: una línea de texto por instrucción (`x = y op z`, `goto`, `param`/`call`, `x[i]`) con temporales `$t` y etiquetas `L`. Este documento justifica las decisiones y muestra cada construcción con salida real. | `tac/instructions.py`, `tac/emitter.py` | `temporales/`, `test_tac_invariantes.py` |
| Declaración y asignación (1) | `let`/`const` con inicializador emiten `x = valor`; sin inicializador no emiten nada. El sombreado se resuelve con nombres únicos por función (`x_1`). | `tac/gen_core.py` | `declaraciones/` |
| Aritméticas (1) | Cada operador es una instrucción de tres direcciones, de izquierda a derecha según la gramática. Un entero usado como `float` pasa por `itof` y `+` entre strings concatena. | `tac/gen_core.py` | `aritmetica/` |
| Lógicas (1) | Las condiciones se compilan a saltos; `&&` y `\|\|` hacen cortocircuito encadenando etiquetas y `!` las intercambia. Como valor se materializa `true`/`false`. | `tac/gen_core.py` (`gen_cond`) | `logicas/` |
| Arreglos (1) | `newarray n` más un `t[i] = v` por elemento; `a[i]` es una carga o un almacenamiento y `len` lo usa `foreach`. Los multidimensionales son arreglos de arreglos. | `tac/gen_core.py` | `arreglos/` |
| Sentencias de control (3) | Ciclos e `if` son etiquetas y saltos, con la condición invertida para ahorrar un `goto`. `foreach` fija dos temporales (longitud e índice), `switch` evalúa una vez y cae de un caso al siguiente, y `break`/`continue` saltan a una pila de etiquetas. | `tac/gen_control.py` | `control_flujo/` |
| Funciones y parámetros (2) | Cada función es una unidad con su propio conjunto de temporales. Una llamada evalúa todos los argumentos, emite los `param` seguidos y luego `call f, n`; se agrega un `return` final si hace falta. | `tac/gen_functions.py` | `funciones/` |
| Recursividad (2) | Es una llamada normal: el símbolo de la función ya existe al generar su cuerpo. Los temporales se reciclan entre llamadas anidadas (`fib(n-1) + fib(n-2)`). | `tac/gen_functions.py` | `recursividad/` |
| Clases y objetos (2) | Una clase es una unidad con un `__init_fields` sintetizado y sus métodos, que reciben `this` primero. `new` reserva el objeto (con la tabla de su clase en `this+0`), inicializa los campos y llama al constructor; los campos son `obj.f`. | `tac/gen_classes.py` | `clases/` |
| Herencia (2) | `__init_fields` llama primero al del padre y los campos heredados conservan su offset. Cada clase declara su `vtable` (slots del padre primero, el override reutiliza el slot) y una llamada a método carga la tabla del objeto y usa `callvirt`, así que se ejecuta el método de la clase real. | `tac/gen_classes.py`, `semantic/layout.py` | `herencia/` |
| try y catch (2) | El TAC marca la región protegida con `try L` / `endtry` / `catch e`. `break`, `continue` y `return` emiten un `endtry` por cada `try` del que salen. | `tac/gen_control.py` | `try_catch/` |
| Reciclaje de temporales (3) | `new_temp()` entrega el menor índice libre del conjunto de la función. Quien consume un operando lo libera justo después de emitir, y al cerrar cada función se detecta cualquier fuga. | `tac/emitter.py` | `temporales/`, `test_tac_invariantes.py` |
| Tabla de símbolos (2) | Tras generar el TAC, `layout.py` da a cada símbolo tamaño, offset, dirección (`gp+`, `fp±`, `this+`) y nombre en el TAC. Cada función y `__main` recibe su registro de activación, y cada clase su layout de campos y métodos. | `semantic/layout.py`, `semantic/symbols.py` | `tabla_simbolos/` |

## 14. Autoría (Proyecto 2)

El generador se escribió como un visitor aparte compuesto por cuatro *mixins*, y
cada regla de la gramática tiene un solo dueño, así que cada integrante trabaja
en archivos distintos. Este es el reparto acordado en el equipo; la referencia final de quién
escribió cada línea es el historial de commits.

| Integrante | Rúbrica P2 | Archivos | Reglas de la gramática |
|---|---|---|---|
| Camila Richter (`Cami`) | diseño del TAC (3), reciclaje de temporales (3), GUI | `instructions.py`, `emitter.py`, `generator.py`; parche de anotaciones en `checker.py`; integración en `compiler.py`, `main.py` y `server.py`; `frontend/`; `compile_tac` en `conftest.py` y pruebas de `temporales/` | `program`, `statement`, `block` |
| Marinés García (`NESHGP04`) | declaraciones (1), aritmética (1), lógicas (1), arreglos (1), control de flujo (3), try/catch (2) | `gen_core.py`, `gen_control.py`; pruebas de sus áreas | declaraciones, asignaciones, `print`, expresiones y operadores, literales, arreglos, `if`, bucles, `switch`, `break`/`continue`, `try`/`catch` |
| Jose Antonio Mérida (`TonitoMC`) | funciones (2), recursividad (2), clases (2), herencia (2), tabla de símbolos (2) | `gen_functions.py`, `gen_classes.py`, `layout.py`, `symbols.py`; pruebas de `funciones/`, `recursividad/`, `clases/`, `herencia/` y `tabla_simbolos/`; demos de `workspace/input/comp-tac/` | `functionDeclaration`, `returnStatement`, `CallExpr`, `classDeclaration`, `NewExpr`, `ThisExpr`, `PropertyAccessExpr`, `PropertyAssignExpr`, `leftHandSide` |

Para ver el detalle de cualquier archivo: `git log --follow --format='%h %an %s' -- <ruta>`.
