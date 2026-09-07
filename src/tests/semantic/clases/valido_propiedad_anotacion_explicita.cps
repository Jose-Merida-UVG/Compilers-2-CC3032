// Antes de la corrección, una variable con anotación explícita de tipo de
// clase (en vez de inferido con `new`) tenía un ClassType "desconectado"
// del real y no encontraba sus propios miembros.
class Animal {
  var nombre: string;

  function constructor(nombre: string) {
    this.nombre = nombre;
  }
}
let a: Animal = new Animal("Rex");
a.nombre = "Firulais";
print(a.nombre);
