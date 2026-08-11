// Caso de prueba: SINTÁCTICOS, complejidad MEDIA (>= 3 errores sintácticos).

let edad: integer = 20
let nombre: string = "Camila";
let activo: boolean = true;

const limite: integer = 100;

let suma: integer = edad + limite;
let resta: integer = limite - edad;

if edad >= 18) {
  print("mayor de edad");
} else {
  print("menor de edad");
}

let contador: integer = 0;
while (contador < 3) {
  print(contador);
  contador = contador + 1;
}

switch contador) {
  case 3:
    print("llegó a tres");
  default:
    print("otro valor");
}

let numeros: integer[] = [10, 20, 30];
print(numeros[0]);

class Animal {
  var nombre: string;

  function hacerSonido(): string {
    return "...";
  }
}

class Perro: Animal {
  function ladrar(): string {
    return "guau";
  }
}

let a: Animal = new Animal();
let p: Perro = new Perro();

function sumar(x: integer, y: integer): integer {
  return x + y;
}

function saludar(nombrePersona: string): string {
  return "hola " + nombrePersona;
}

print(sumar(edad, limite));
print(saludar(nombre));
