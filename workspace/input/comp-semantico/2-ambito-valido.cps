// Manejo de ámbito — todo correcto, cero errores.
let visible: string = "global";
{
  let visible: string = "sombreada";  // shadowing legal en bloque anidado
  let soloAqui: integer = 2;
  print(visible);
  print(soloAqui);
}
print(visible);                       // vuelve a ser la global

function conAmbitos(p: integer): integer {
  let local: integer = p * 2;
  {
    let masAdentro: integer = local + 1;
    print(masAdentro);
  }
  return local;
}
print(conAmbitos(4));
