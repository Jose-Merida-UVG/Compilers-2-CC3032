function lee(a: integer[], i: integer): integer {
    return a[i];
}
let total: integer = 0;
let datos = [10, 20];
try {
    total = total + lee(datos, 0);
    total = total + lee(datos, 5);
    total = total + 1000;
} catch (e) {
    print("capturada");
}
print(total);
