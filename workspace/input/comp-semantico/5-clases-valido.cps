// Clases y objetos — todo correcto, cero errores.
class Animal {
  var nombre: string;
  var edad: integer;
  const PATAS: integer = 4;

  function constructor(nombre: string, edad: integer) {
    this.nombre = nombre;
    this.edad = edad;
  }

  function describir(): string { return this.nombre; }
}

class Perro : Animal {
  var raza: string;
  function ladrar(): string { return this.nombre + " dice guau"; }
}

let animal: Animal = new Animal("Genérico", 3);
let perro: Perro = new Perro("Fido", 2);   // constructor heredado

let leido: string = perro.nombre;          // atributo heredado
let patas: integer = perro.PATAS;          // constante heredada
let ladrido: string = perro.ladrar();      // método propio
let desc: string = perro.describir();      // método heredado

perro.raza = "labrador";                   // escritura de atributo propio
perro.edad = perro.edad + 1;               // lectura + escritura heredada

let comoBase: Animal = perro;              // subclase asignable a la base
let nulo: Animal = null;                   // null en tipo clase
print(ladrido);
print(desc);
