// Control de flujo — todo correcto, cero errores.
let n: integer = 5;

if (n > 10) { print("mayor"); } else { print("menor"); }

let i: integer = 0;
while (i < 3) {
  i = i + 1;
  if (i == 1) { continue; }
  if (i == 3) { break; }
}

do { i = i - 1; } while (i > 0);

// Las dos cláusulas centrales del 'for' son opcionales por separado.
for (let a: integer = 0; a < 3; a = a + 1) { }
for (let b: integer = 0; b < 3; ) { }
for (let c: integer = 0; ; c = c + 1) { break; }
for (; ; ) { break; }

switch (n) {
  case 5:
    print("cinco");
  case 0:
    print("cero");
  default:
    print("otro");
}

try { print("intenta"); } catch (err) { print("falló"); }
