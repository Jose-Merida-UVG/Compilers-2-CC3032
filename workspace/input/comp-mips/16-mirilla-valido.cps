// Demo — mirilla (peephole): un programa que activa varias de las reglas. Correr con ▶,
// abrir la pestaña "asm" y alternar "Sin mirilla" / "Con mirilla"; arriba salen los contadores.

function mostrar(n: integer) { print(n); }
function gcd(a: integer, b: integer): integer {
    if (b == 0) { return a; }
    return gcd(b, a % b);
}

// llamadas seguidas: los ajustes de $sp se fusionan
mostrar(1);
mostrar(2);
mostrar(3);

// break dentro de un if: la rama salta sobre un salto
let i: integer = 0;
while (i < 10) {
    if (i == 3) { break; }
    i = i + 1;
}
print(i);

// if/else dentro de un ciclo: un salto cae en otro salto
let pares: integer = 0;
for (let k: integer = 0; k < 6; k = k + 1) {
    if (k % 2 == 0) { pares = pares + 1; } else { continue; }
}
print(pares);

// && y ||: cortocircuito (no activa ninguna regla propia; el código muerto sale en el demo 17)
let a: integer = 2;
let b: integer = 3;
if (a < b && b > 0 || a == 0) { print("ok"); }

// sumar cero a un resultado temporal es una identidad
let r: integer = (a * b) + 0;
print(r);
print(gcd(48, 18));
