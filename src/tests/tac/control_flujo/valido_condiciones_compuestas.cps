let a: integer = 3;
let b: integer = 9;
let c: boolean = false;
if (a < b && b < 10) {
    print("rango");
}
if (a > b || c) {
    print("o");
} else {
    print("ninguno");
}
if ((a < b || c) && !c) {
    print("mixto");
}
while (a < b && !c) {
    a = a + 1;
}
