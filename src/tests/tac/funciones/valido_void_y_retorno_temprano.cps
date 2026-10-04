function mostrar(n: integer) {
    if (n < 0) { print("negativo"); return; }
    print(n);
}
function signo(n: integer): integer {
    if (n > 0) { return 1; } else {
        if (n < 0) { return -1; } else { return 0; }
    }
}
mostrar(-1);
mostrar(5);
print(signo(3));
