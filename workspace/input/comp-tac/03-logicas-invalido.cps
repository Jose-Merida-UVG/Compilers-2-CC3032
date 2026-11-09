// Demo — expresiones lógicas con cortocircuito y ternario con errores: no se genera TAC.
let a = "a" < "b";
let b = true > false;
let x: integer = 5;
let t = x ? 1 : 2;           // la condición del ternario debe ser boolean
let u = x < 9 ? 1 : "dos";   // las ramas deben tener tipos compatibles
