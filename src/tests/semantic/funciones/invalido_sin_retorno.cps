// Una función con tipo de retorno declarado debe retornar en todos sus
// caminos. Un 'if' sin 'else' no garantiza nada.
function sinRetorno(): integer {
  print("no retorna");
}
function soloUnaRama(n: integer): integer {
  if (n > 0) { return 1; }
}
