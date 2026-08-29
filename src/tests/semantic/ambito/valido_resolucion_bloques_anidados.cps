// Resolución de nombres a través de bloques anidados: una variable
// declarada en un bloque exterior debe poder leerse y usarse desde
// bloques interiores, sin necesidad de volver a declararla.
let x: integer = 1;
{
  let y: integer = x + 1;
  {
    print(x);
    print(y);
  }
}
