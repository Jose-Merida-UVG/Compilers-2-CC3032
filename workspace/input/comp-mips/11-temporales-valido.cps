// Demo — reciclaje de temporales. Correr con ▶ y mirar la pestaña "tac".
let a: integer = 1;
let b: integer = 2;
let c: integer = 3;
let d: integer = 4;
let e: integer = 5;
let f: integer = 6;
let suma = a + b + c + d + e + f;
let mezcla = ((a + b) * (c - d)) / ((e + f) * (a - b));
let profunda = a + (b * (c + (d * (e + f))));
print(suma + mezcla + profunda);
