let total: string = "hola";

function sumarTodos(valores: integer[]): integer {
  let total: integer = 0;
  foreach (v in valores) {
    total = total + v;
  }
  return total;
}