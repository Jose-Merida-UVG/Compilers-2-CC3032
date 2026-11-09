// Una función declarada dentro de un bucle no hereda el bucle: su `break` no es válido.
let i: integer = 0;
while (i < 3) {
  function f() {
    break;
  }
  i = i + 1;
}
