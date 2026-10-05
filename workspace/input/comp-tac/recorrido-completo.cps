// Demo — recorrido completo: una muestra de cada punto de la rúbrica en un solo archivo.
// Correr con ▶ y mirar las pestañas "tac" y "symbols" (frames, offsets, vtable).

// --- Globales: viven en gp (gp+0, gp+4, ...), no en un frame. Constantes igual.
const LIMITE: integer = 3;
let total: integer = 0;
let precio: float = 2.5;

// --- Aritmética y promoción: integer -> float con itof; los temporales se reciclan.
let mezcla: float = total + precio * 2;

// --- Lógicas: cortocircuito con saltos, sin materializar el booleano.
let ok: boolean = total < LIMITE && (precio > 1.0 || total == 0);

// --- Funciones: cada una tiene su frame. Parámetros en fp+8.., locales en fp-4..
function suma(a: integer, b: integer): integer {
    let s: integer = a + b;
    return s;
}

// --- Recursividad: llamada normal; los temporales se reciclan entre llamadas anidadas.
function fib(n: integer): integer {
    if (n < 2) { return n; }
    return fib(n - 1) + fib(n - 2);
}

// --- Clase: campos desde this+4 (this+0 es la tabla de métodos). Métodos reciben this.
class Cuenta {
    var saldo: integer = 100;
    function depositar(m: integer): integer {
        saldo = saldo + m;        // campo sin this. -> this.saldo
        return this.saldo;
    }
    function tipo(): string { return "base"; }
}

// --- Herencia: el campo heredado conserva su offset; el override (tipo) reutiliza el slot 1.
class Ahorro : Cuenta {
    var tasa: integer = 2;
    function tipo(): string { return "ahorro"; }
}

// --- Objetos: new + __init_fields; x.f = y / x = y.f; callvirt por la vtable.
let c: Cuenta = new Ahorro();
c.saldo = 50;
total = c.depositar(suma(total, 10));
print(c.tipo());                  // despacho dinámico: Ahorro.tipo

// --- Arreglos y control de flujo.
let datos: integer[] = [fib(5), fib(6), 3];
let i: integer = 0;
while (i < 3) {
    if (datos[i] > 4) { total = total + datos[i]; }
    i = i + 1;
}
for (let k: integer = 0; k < 2; k = k + 1) { print(k); }
foreach (d in datos) { print(d); }
switch (total) {
    case 0: print("cero");
    default: print("otro");
}

// --- try / catch: región protegida.
try {
    print(datos[1]);
} catch (e) {
    print(e);
}
