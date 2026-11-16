// Demo — herencia con errores: no se genera TAC.
class Perro : Animal { }                 // clase base no declarada
class Animal2 { }
class Gato : Animal2 { function maullar(): string { return "miau"; } }
let a: Animal2 = new Animal2();
print(a.maullar());                      // el método es de la subclase
let g: Gato = new Animal2();             // padre asignado a hijo
