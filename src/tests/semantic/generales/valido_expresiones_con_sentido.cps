// Contraparte válida de los casos inválidos de esta carpeta: expresiones
// que sí tienen sentido semántico, sin código muerto ni duplicados.
function doble(x: integer): integer {
  return x * 2;
}
var n: integer = doble(3) + 1;
var texto: string = "hola " + "mundo";
var flag: boolean = n > 0 && !false;
while (n > 0) {
  n = n - 1;
  if (n == 2) { continue; }
}
