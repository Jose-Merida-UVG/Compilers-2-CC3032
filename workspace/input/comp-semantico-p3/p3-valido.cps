// Caso de prueba: Persona 3 (control de flujo, clases, arreglos) -- válido.
// No debería reportar ningún error semántico.

class Animal {
  var nombre: string;
  var edad: integer;

  function constructor(nombre: string, edad: integer) {
    this.nombre = nombre;
    this.edad = edad;
  }

  function describir(): string {
    return this.nombre;
  }
}

class Perro: Animal {
  function ladrar(): string {
    return "guau";
  }
}

let mascota = new Perro("Rex", 3);
print(mascota.describir());
print(mascota.ladrar());

let numeros: integer[] = [1, 2, 3, 4, 5];
let suma: integer = 0;
let i: integer = 0;

while (i < 5) {
  suma = suma + numeros[i];
  if (numeros[i] == 3) {
    i = i + 1;
    continue;
  }
  i = i + 1;
}

for (let j: integer = 0; j < 5; j = j + 1) {
  if (j == 4) {
    break;
  }
  print(numeros[j]);
}

switch (suma) {
  case 15:
    print("suma esperada");
  default:
    print("suma distinta");
}

function sumarPares(valores: integer[]): integer {
  let total: integer = 0;
  let k: integer = 0;
  while (k < 5) {
    if (valores[k] % 2 == 0) {
      total = total + valores[k];
    }
    k = k + 1;
  }
  return total;
}

print(sumarPares(numeros));
