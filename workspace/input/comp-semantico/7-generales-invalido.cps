// Generales — un error por línea marcada con [n].
function muerto(): integer {
  return 1;
  print("nunca");                    // [1] código muerto
}
function sumar(a: integer, b: integer): integer { return a + b; }
function multiplicaFuncion(): integer { return sumar * 2; } // [2] multiplicar una función
let dup: integer = 1;
let dup: integer = 2;                // [3] declaración duplicada
function paramDup(p: integer, p: integer): integer { return p; } // [4] parámetro duplicado
