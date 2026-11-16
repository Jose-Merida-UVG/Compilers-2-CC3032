let x: integer = 1;
let a = [1];
try {
    x = 2;
    x = x + 3;
    print(a[7]);
} catch (e) {
    print(x);
}
