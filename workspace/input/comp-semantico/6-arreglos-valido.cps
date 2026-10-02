// Arreglos — todo correcto, cero errores.
let numeros: integer[] = [1, 2, 3];
let decimales: float[] = [1.5, 2];        // integer se promueve a float
let vacio: integer[] = [];                // arreglo vacío en cualquier arreglo
let matriz: integer[][] = [[1, 2], [3]];
let matrizVacia: integer[][] = [[]];      // vacío anidado
let cadenas: string[] = ["a", "b"];
let primero: integer = numeros[0];
let celda: integer = matriz[1][0];

foreach (n in numeros) {
  print(n + 1);                            // n es integer
}

function sumarTodos(valores: integer[]): integer {
  let total: integer = 0;
  foreach (v in valores) { total = total + v; }
  return total;
}
print(sumarTodos(numeros));
