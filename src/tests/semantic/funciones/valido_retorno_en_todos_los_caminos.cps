// Formas que sí garantizan retorno; y una función sin anotación es void,
// así que no se le exige nada.
function directo(): integer { return 1; }
function ambasRamas(n: integer): integer {
  if (n > 0) { return 1; } else { return 2; }
}
function despuesDelIf(n: integer): integer {
  if (n > 0) { print("positivo"); }
  return 0;
}
function esVoid() { print("sin retorno declarado"); }
