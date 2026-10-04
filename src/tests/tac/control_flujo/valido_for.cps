let total: integer = 0;
for (let i: integer = 0; i < 5; i = i + 1) {
    total = total + i;
}
let j: integer = 0;
for (j = 10; j > 0; j = j - 2) {
    print(j);
}
for (let k: integer = 0; k < 3;) {
    k = k + 1;
}
let v: integer = 0;
for (; v < 4; v = v + 1) {
    print(v);
}
for (let w: integer = 0; w < 2; w = w + 1) {
    for (let z: integer = 0; z < 2; z = z + 1) {
        print(w * 2 + z);
    }
}
