// Demo — expresiones aritméticas, precedencia y promoción a float. Correr con ▶ y mirar la pestaña "tac".
let a: integer = 2;
let b: integer = 3;
let c: integer = 4;
let d: integer = 5;
let r1 = a + b * c;
let r2 = a * b + c * d;
let r3 = (a + b) * (c - d);
let r4 = a + b + c + d;
let r5 = a - b - c;
let r6 = a * b / c % d;
print(r1 + r2 + r3);
