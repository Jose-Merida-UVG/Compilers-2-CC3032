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
print(gcd(48, 18));
hanoi(2, "A", "C", "B");
