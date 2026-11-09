let v: integer[] = [1, 2, 3, 4, 5];
let s: integer = 0;
for (let i: integer = 0; i < 5; i = i + 1) {
    s = s + v[i];
}
print(s);
foreach (x in v) {
    print(x * x);
}
