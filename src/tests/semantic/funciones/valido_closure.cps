function crearContador(): integer {
  let x: integer = 0;
  function siguiente(): integer {
    x = x + 1;
    return x;
  }
  return siguiente() + siguiente();
}
print(crearContador());
