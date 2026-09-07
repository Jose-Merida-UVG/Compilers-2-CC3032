// Manejo de ámbito — un error por línea marcada con [n].
noExiste = 1;                        // [1] asignar a variable no declarada
let usada: integer = noDeclarada;    // [2] leer variable no declarada
let dup: integer = 1;
let dup: integer = 2;                // [3] redeclaración en el mismo ámbito
class C { }
class C { }                          // [4] redeclaración de clase
{
  let interna: integer = 1;
}
let fuera: integer = interna;        // [5] la variable murió al cerrar el bloque
