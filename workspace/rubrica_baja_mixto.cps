// Caso de prueba: MIXTO, complejidad BAJA (>= 2 léxicos y >= 2 sintácticos).

let edad@ integer = 20;
let nombre: string = "Camila"
let activo: boolean = true;

const limite: integer = 100;

let suma: integer = edad + limite;
let resta: integer = limite # edad;

if (edad >= 18 {
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
