class Base {
  function metodo(): integer {
    return 1;
  }
}

class Derivada: Base {
  function otro(): integer {
    return 2;
  }
}

let d = new Derivada();
let x: integer = d.metodo();
let y: integer = d.otro();
