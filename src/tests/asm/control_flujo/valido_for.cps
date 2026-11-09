let s: integer = 0;
for (let i: integer = 1; i <= 5; i = i + 1) {
    s = s + i;
}
print(s);
for (let j: integer = 10; j > 0; j = j - 3) {
    print(j);
}
let k: integer = 0;
for (;;) {
    k = k + 1;
    if (k == 3) {
        break;
    }
}
print(k);
