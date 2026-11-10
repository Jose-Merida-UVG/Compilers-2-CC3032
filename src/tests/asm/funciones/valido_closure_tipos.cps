function mensaje(activo: boolean, nombre: string, factor: float): string {
    let veces: integer = 0;
    function saluda(): string {
        veces = veces + 1;
        if (activo) {
            return "hola " + nombre;
        }
        return "adios " + nombre;
    }
    let a: string = saluda();
    let b: string = saluda();
    print(veces);
    print(factor * 2.0);
    return a + "/" + b;
}
print(mensaje(true, "ana", 1.5));
print(mensaje(false, "luis", 0.5));
