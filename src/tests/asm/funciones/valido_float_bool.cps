function promedio(a: float, b: float): float {
    return (a + b) / 2;
}
function elige(flag: boolean, x: integer, y: integer): integer {
    if (flag) {
        return x;
    }
    return y;
}
function esPar(n: integer): boolean {
    return n % 2 == 0;
}
print(promedio(2.0, 3.0));
print(promedio(1, 2));
print(elige(true, 1, 2));
print(elige(false, 1, 2));
print(esPar(4));
print(esPar(7));
