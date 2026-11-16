// Demo — recursividad con errores: no se genera TAC.
function f(n: integer): integer {
    if (n == 0) { return "cero"; }   // tipo de retorno
    return f(n, 1);                  // argumentos de más
}
