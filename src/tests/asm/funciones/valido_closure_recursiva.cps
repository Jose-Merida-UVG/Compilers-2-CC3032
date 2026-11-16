function cuenta(n: integer): integer {
    let pasos: integer = 0;
    function baja(k: integer): integer {
        pasos = pasos + 1;
        if (k <= 0) {
            return pasos;
        }
        return baja(k - 1);
    }
    return baja(n);
}
print(cuenta(4));
