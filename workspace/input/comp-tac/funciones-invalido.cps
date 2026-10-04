// Demo — funciones con errores: no se genera TAC.
function f(a: integer): integer { return a; }
print(f(1, 2));          // argumentos de más
print(f("x"));           // tipo de argumento
function g(a: integer): integer {
    if (a > 0) { return 1; }   // falta retorno en un camino
}
let x = 1;
x();                     // no es una función
