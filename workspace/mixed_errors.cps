// Caso de prueba: errores léxicos y sintácticos mezclados,
// incluyendo construcciones anidadas (clase con métodos y control de flujo).

class Persona {
  var nombre: string;
  var edad$ integer;

  function saludar(): string {
    if (this.edad > 0 {
      return "hola";
    }
    return "adiós";
  }
}

let p: integer = 10;
switch (p) {
  case 1
    print("uno");
  case 2:
    print("dos");
  default:
    print(p & 1);
}

function factorial(n: integer): integer {
  if (n <= 1) {
    return 1;
  }
  return n * factorial(n - 1);
}

print(factorial(5));
