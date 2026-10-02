// Caso de prueba: Persona 3, clases y arreglos -- inválido.
// Cada bloque dispara una regla distinta; se espera más de un error semántico.

class Animal {
  var nombre: string;

  function constructor(nombre: string) {
    this.nombre = nombre;
  }
}

// Miembro que no existe.
let a = new Animal("Rex");
let especie = a.especie;

// Argumentos de constructor incorrectos.
let b = new Animal();

// Clase no declarada.
let c = new Fantasma();

// 'this' fuera de una clase.
function f(): string {
  return this.nombre;
}

// Indexar algo que no es un arreglo.
let n: integer = 5;
let y = n[0];

// Índice que no es integer.
let numeros: integer[] = [1, 2, 3];
let z = numeros["cero"];

// Elementos de arreglo con tipos incompatibles.
let mezcla = [1, true, "tres"];
