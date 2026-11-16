// Mirilla — salto_a_salto: un salto cuyo destino es otro salto va directo al final.
// El `continue` salta a una etiqueta que a su vez solo salta al paso del `for`.
let pares: integer = 0;
for (let k: integer = 0; k < 6; k = k + 1) {
    if (k % 2 == 0) { pares = pares + 1; } else { continue; }
}
print(pares);
