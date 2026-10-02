// Funciones — un error por línea marcada con [n].
function sumar(a: integer, b: integer): integer { return a + b; }
sumar(1);                            // [1] faltan argumentos
sumar(1, "dos");                     // [2] tipo de argumento
let noEsFn: integer = 1;
noEsFn();                            // [3] invocar algo que no es función
function sumar(x: integer): integer { return x; }   // [4] sin sobrecarga
function malRetorno(): integer { return "texto"; }  // [5] tipo de retorno
function paramDup(p: integer, p: integer): integer { return p; } // [6] parámetro duplicado
function sinRetornar(): integer { print("nada"); }  // [7] no retorna en todos los caminos
function soloUnaRama(n: integer): integer {   // [8] un 'if' sin 'else' no garantiza retorno
  if (n > 0) { return 1; }
}
