function primero(a: integer[]): integer {
    return a[0];
}
function repite(s: string): string {
    return s + s;
}
function modifica(a: integer[]) {
    a[0] = 100;
}
print(primero([7, 8, 9]));
print(repite("ab"));
let v: integer[] = [1, 2];
modifica(v);
print(v[0]);
