// Una función anidada no puede redeclarar un nombre ya usado en el
// mismo ámbito (el de la función que la contiene), aunque capture
// variables de ese entorno.
function externa(): integer {
  let contador: integer = 0;
  function contador(): integer {
    return contador;
  }
  return contador();
}
