let notas = [10, 20, 30];
let suma: integer = 0;
foreach (n in notas) {
    suma = suma + n;
}
print(suma);
let nombres = ["ana", "luis"];
foreach (nombre in nombres) {
    print("hola " + nombre);
}
let m = [[1, 2], [3, 4]];
foreach (fila in m) {
    foreach (v in fila) {
        print(v);
    }
}
foreach (x in [5, 6, 7]) {
    if (x == 6) {
        continue;
    }
    if (x > 6) {
        break;
    }
    print(x);
}
