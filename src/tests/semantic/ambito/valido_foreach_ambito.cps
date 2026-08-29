// El ámbito del foreach: la variable del ciclo debe existir y resolverse
// correctamente dentro de su propio bloque.
let numeros: integer[] = [10, 20, 30];
foreach (n in numeros) {
  print(n);
}
