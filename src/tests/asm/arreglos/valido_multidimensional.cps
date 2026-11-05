let m: integer[][] = [[1, 2, 3], [4, 5, 6]];
print(m[0][2]);
print(m[1][0]);
m[1][1] = 50;
let total: integer = 0;
foreach (fila in m) {
    foreach (v in fila) {
        total = total + v;
    }
}
print(total);
