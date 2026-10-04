function sumar(a: integer[], i: integer, n: integer): integer {
    if (i >= n) { return 0; }
    return a[i] + sumar(a, i + 1, n);
}
let xs = [1, 2, 3, 4];
print(sumar(xs, 0, 4));
