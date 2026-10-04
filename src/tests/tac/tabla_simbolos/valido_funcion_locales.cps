function mezcla(a: integer, b: boolean, c: float): integer {
    let x: integer = a;
    let activo: boolean = b;
    let y: float = c;
    {
        let z: integer = x + 1;
        x = z;
    }
    if (activo) { return x; }
    return mezcla(x, false, y);
}
print(mezcla(1, true, 2.0));
