// Mirilla — salto_sobre_salto: `beq x,y,L1 / j L2 / L1:` pasa a `bne x,y,L2 / L1:`.
// El `break` dentro de un `if` produce una rama que salta sobre un salto.
let i: integer = 0;
while (i < 10) {
    if (i == 4) { break; }
    i = i + 1;
}
print(i);
