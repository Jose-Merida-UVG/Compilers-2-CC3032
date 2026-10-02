// Generales — todo correcto, cero errores.
function doble(x: integer): integer { return x * 2; }
let n: integer = doble(3) + 1;
let texto: string = "hola " + "mundo";
let flag: boolean = n > 0 && !false;
while (n > 0) {
  n = n - 1;
  if (n == 2) { continue; }
}
print(n);
