let a: integer = 1;
let b: integer = 2;
let c: integer = 3;
let d: integer = 4;
let e: integer = 5;
let r = ((a + b) * (c + d)) - ((e - a) * (b + c)) + (a * b * c * d * e);
print(r);
a = b + c * d;
b = (a + b) * (c + d);
