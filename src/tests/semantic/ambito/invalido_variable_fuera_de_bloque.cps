// La variable del foreach solo debe existir dentro de su propio bloque;
// usarla después de que el bloque termina debe reportar error.
let numeros: integer[] = [1, 2, 3];
foreach (n in numeros) {
  print(n);
}
print(n);
