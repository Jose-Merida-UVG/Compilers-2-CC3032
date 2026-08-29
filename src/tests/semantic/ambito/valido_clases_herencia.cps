// Herencia de clases: la clase base debe existir y quedar registrada
// como el padre de la subclase. Miembros con el mismo nombre en clases
// distintas no deben chocar entre sí (cada clase tiene su propio ámbito).
class Animal {
  var nombre: string;
}

class Perro: Animal {
  var nombre: string;
}
