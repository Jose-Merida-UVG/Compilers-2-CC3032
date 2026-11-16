// Mirilla — move_ida_y_vuelta: `move a,b` seguido de `move b,a` deja solo el primero.
// Pasa al devolver el resultado de una llamada.
function gcd(a: integer, b: integer): integer {
    if (b == 0) { return a; }
    return gcd(b, a % b);
}
print(gcd(48, 18));
