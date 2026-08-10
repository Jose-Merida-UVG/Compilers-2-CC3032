// Caso de prueba: solo errores léxicos, en distintas líneas.
let a: integer = 5;
let b @ integer = 10;

print(a # b);

let c: string = "cadena sin cerrar;
print(c);

let d~ integer = 1;
print(d);
