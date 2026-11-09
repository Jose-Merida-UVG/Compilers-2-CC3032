function doble(n: integer): integer {
    return n * 2;
}
function suma(a: integer, b: integer): integer {
    return a + b;
}
function seis(a: integer, b: integer, c: integer, d: integer, e: integer, f: integer): integer {
    return a + b * 10 + c * 100 + d * 1000 + e * 10000 + f * 100000;
}
function externa(n: integer): integer {
    function interna(m: integer): integer {
        return m + 1;
    }
    let r: integer = interna(n);
    return r * 2;
}
print(suma(doble(2), doble(3)));
print(seis(1, 2, 3, 4, 5, 6));
print(externa(3));
