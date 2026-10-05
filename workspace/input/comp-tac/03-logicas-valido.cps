// Demo — expresiones lógicas con cortocircuito y ternario. Correr con ▶ y mirar la pestaña "tac".
let a: boolean = true;
let b: boolean = false;
let c: boolean = true;
let x: integer = 5;
let y: integer = 9;
let r1 = a && b;
let r2 = a || b;
let r3 = a && b || c;
let r4 = a || b && c;
let r5 = (a || b) && c;
let r6 = x < y && y < 10;
let r7 = x > y || x == 5;
let r8 = a && b && c;
let r9 = a || b || c;
let r10 = x < y && (a || b) && !c;
print(r1 && r2);
