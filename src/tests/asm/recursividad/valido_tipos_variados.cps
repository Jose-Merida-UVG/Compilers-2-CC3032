function suma(a: integer[], i: integer): integer {
    if (i >= 3) {
        return 0;
    }
    return a[i] + suma(a, i + 1);
}
function potencia(b: integer, e: integer): integer {
    if (e == 0) {
        return 1;
    }
    return b * potencia(b, e - 1);
}
function potf(x: float, n: integer): float {
    if (n == 0) {
        return 1.0;
    }
    return x * potf(x, n - 1);
}
function repite(s: string, n: integer): string {
    if (n == 0) {
        return "";
    }
    return s + repite(s, n - 1);
}
print(suma([4, 5, 6], 0));
print(potencia(2, 10));
print(potf(1.5, 2));
print(repite("ab", 3));
