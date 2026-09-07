// Las dos cláusulas centrales del 'for' son opcionales por separado, así
// que con una sola presente hay que distinguir por posición y no por
// cantidad: con solo incremento, ese incremento NO es la condición.
for (let a: integer = 0; a < 3; a = a + 1) { }
for (let b: integer = 0; b < 3; ) { }
for (let c: integer = 0; ; c = c + 1) { break; }
for (let d: integer = 0; ; ) { break; }
for (; ; ) { break; }
