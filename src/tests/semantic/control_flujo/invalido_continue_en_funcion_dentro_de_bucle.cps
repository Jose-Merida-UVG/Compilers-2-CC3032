// Ni el `continue`: la función no hereda el bucle que la rodea.
let i: integer = 0;
while (i < 3) {
  function f() {
    continue;
  }
  i = i + 1;
}
