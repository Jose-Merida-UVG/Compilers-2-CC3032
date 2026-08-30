// Expresión sin sentido semántico: una función no es un valor numérico,
// no se puede multiplicar.
function f(): integer { return 1; }
let x = f * 2;
