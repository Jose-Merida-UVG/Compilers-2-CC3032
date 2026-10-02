function suma(a: integer, b: integer): integer {
  return a + b;
}
function saludar(nombre: string): string {
  return "Hola " + nombre;
}
function factorial(n: integer): integer {
  if (n <= 1) { return 1; }
  return n * factorial(n - 1);
}
print(suma(1, 2));
print(saludar("Mundo"));
print(factorial(5));
