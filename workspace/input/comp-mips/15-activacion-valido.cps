// Llamadas anidadas, recursión y un método: el árbol y los registros de activación.
class Calc {
    function doble(x: integer): integer { return x * 2; }
}
function fib(n: integer): integer {
    if (n < 2) { return n; }
    return fib(n - 1) + fib(n - 2);
}
function cuadrado(n: integer): integer { return n * n; }
function combina(a: integer, b: integer, c: integer): integer {
    return cuadrado(a) + cuadrado(b) + fib(c);
}
let calc = new Calc();
print(combina(3, 4, 10));
print(calc.doble(21));
print(fib(7));
