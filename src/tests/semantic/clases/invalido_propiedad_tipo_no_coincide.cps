// Regresión: la asignación a propiedad debe validar tipo y existencia,
// tanto con la variable tipada por anotación explícita como por inferencia.
class Animal {
  var nombre: string;
}
let a: Animal = new Animal();
a.nombre = 5;
