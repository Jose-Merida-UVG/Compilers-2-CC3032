// Caso de prueba: Persona 3, control de flujo -- inválido.
// Cada bloque dispara una regla distinta; se espera más de un error semántico.

let x: integer = 5;

// Condición no boolean en if/while/for.
if (x) {
  print("mal");
}

while (x) {
  x = x - 1;
}

for (let i: integer = 0; i; i = i + 1) {
  print(i);
}

// break/continue fuera de un bucle.
break;
continue;

// return fuera de una función.
return x;

// Código muerto: nada después de esto debería ejecutarse.
function f(): integer {
  return 1;
  let inalcanzable: integer = 2;
}
