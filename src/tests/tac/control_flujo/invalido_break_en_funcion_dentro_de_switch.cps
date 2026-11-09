// Lo mismo con un switch: la función no hereda el `break` del switch que la rodea.
let a: integer = 1;
switch (a) {
  case 1:
    function g() {
      break;
    }
    break;
}
