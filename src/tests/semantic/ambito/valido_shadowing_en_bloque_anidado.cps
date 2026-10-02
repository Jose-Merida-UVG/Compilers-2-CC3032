// Shadowing: declarar una variable con el mismo nombre que una del
// ámbito exterior, dentro de un bloque anidado, es válido (no es la
// misma variable, así que no cuenta como redeclaración).
let x: integer = 1;
{
  let x: integer = 2;
  print(x);
}
print(x);
