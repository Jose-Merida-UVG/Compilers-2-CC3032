// Clases y objetos — un error por línea marcada con [n].
class Animal {
  var nombre: string;
  const PATAS: integer = 4;
  function constructor(nombre: string) { this.nombre = nombre; }
}
class Perro : Animal { }
let perro: Perro = new Perro("Fido");
perro.noExisteMiembro;               // [1] miembro inexistente (lectura)
perro.nombre = 99;                   // [2] escritura: tipo incompatible
perro.tampocoExiste = 1;             // [3] escritura: miembro inexistente
perro.PATAS = 8;                     // [4] escritura sobre constante
let n: integer = 3;
n.campo = 1;                         // [5] '.' sobre algo que no es objeto
new NoDeclarada();                   // [6] clase no declarada
new Animal();                        // [7] constructor: faltan argumentos
new Animal(7);                       // [8] constructor: tipo de argumento
this;                                // [9] 'this' fuera de clase
class Hija : NoExiste { }            // [10] clase base no declarada
