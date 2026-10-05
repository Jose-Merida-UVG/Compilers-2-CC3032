// Demo — recursividad: factorial, fibonacci, gcd, Hanoi, suma de arreglo
// y recursión dentro de un método.
function fact(n: integer): integer {
    if (n <= 1) { return 1; }
    return n * fact(n - 1);
}
function fib(n: integer): integer {
    if (n < 2) { return n; } else { return fib(n - 1) + fib(n - 2); }
}
function gcd(a: integer, b: integer): integer {
    if (b == 0) { return a; }
    return gcd(b, a % b);
}
function hanoi(n: integer, origen: string, destino: string, auxiliar: string) {
    if (n == 0) { return; }
    hanoi(n - 1, origen, auxiliar, destino);
    print(origen + " -> " + destino);
    hanoi(n - 1, auxiliar, destino, origen);
}
function sumar(a: integer[], i: integer, n: integer): integer {
    if (i >= n) { return 0; }
    return a[i] + sumar(a, i + 1, n);
}
class Calc {
    function fact(n: integer): integer {
        if (n <= 1) { return 1; }
        return n * this.fact(n - 1);
    }
}

print(fact(5));
print(fib(7));
print(gcd(48, 18));
hanoi(2, "A", "C", "B");
print(sumar([1, 2, 3, 4], 0, 4));
print(new Calc().fact(5));
