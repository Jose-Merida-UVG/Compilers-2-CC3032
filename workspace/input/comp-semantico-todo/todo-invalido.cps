// ============================================================
//  Batería completa de errores semánticos — un error por línea
//  marcada con [n]. El archivo es sintácticamente válido a
//  propósito: si hubiera un error de sintaxis, el análisis
//  semántico ni siquiera correría.
// ============================================================

// ---------- Declaraciones base (válidas) --------------------
class Animal {
  var nombre: string;
  const PATAS: integer = 4;
  function constructor(nombre: string) { this.nombre = nombre; }
  function describir(): string { return this.nombre; }
}
class Perro : Animal {
  function ladrar(): string { return "guau"; }
}
function sumar(a: integer, b: integer): integer { return a + b; }

// ---------- Sistema de tipos --------------------------------
let t1: integer = "texto";           // [1] asignación: tipo no coincide
let t2: integer = 1 + true;          // [2] aritmética con boolean
let t3: boolean = 1 && true;         // [3] lógica con integer
let t4: boolean = "a" < 3;           // [4] comparación incompatible
let t5: boolean = 5 == "cinco";      // [5] igualdad incompatible
let t6: integer = -"x";              // [6] unario '-' sobre string
let t7: boolean = !5;                // [7] unario '!' sobre integer
let t8: integer = true ? 1 : 2;      // ok
let t9: integer = 5 ? 1 : 2;         // [8] condición de ternario no boolean

// ---------- Ámbito ------------------------------------------
noExiste = 1;                        // [9] asignar a variable no declarada
let usada: integer = noDeclarada;    // [10] leer variable no declarada
let dup: integer = 1;
let dup: integer = 2;                // [11] redeclaración en el mismo ámbito

// ---------- Funciones ---------------------------------------
sumar(1);                            // [12] faltan argumentos
sumar(1, "dos");                     // [13] tipo de argumento
let noEsFn: integer = 1;
noEsFn();                            // [14] invocar algo que no es función
function sumar(x: integer): integer { return x; }   // [15] sin sobrecarga
function malRetorno(): integer { return "texto"; }  // [16] tipo de retorno
function paramDup(p: integer, p: integer): integer { return p; } // [17] parámetro duplicado

// ---------- Control de flujo --------------------------------
if (1) { }                           // [18] condición de if
while ("x") { }                      // [19] condición de while
do { } while (5);                    // [20] condición de do-while
for (let i: integer = 0; 7; ) { }    // [21] condición de for
switch (1) { case "s": print(1); }   // [22] case incompatible con switch
break;                               // [23] break fuera de bucle
continue;                            // [24] continue fuera de bucle
return 1;                            // [25] return fuera de función

// ---------- Clases y objetos --------------------------------
let perro: Perro = new Perro("Fido");   // ok: hereda el constructor de Animal
perro.noExisteMiembro;               // [26] miembro inexistente (lectura)
perro.nombre = 99;                   // [27] escritura: tipo incompatible
perro.tampocoExiste = 1;             // [28] escritura: miembro inexistente
perro.PATAS = 8;                     // [29] escritura sobre constante
let n: integer = 3;
n.campo = 1;                         // [30] '.' sobre algo que no es objeto
new NoDeclarada();                   // [31] clase no declarada
new Animal();                        // [32] constructor: faltan argumentos
new Animal(7);                       // [33] constructor: tipo de argumento
this;                                // [34] 'this' fuera de clase

// ---------- Arreglos ----------------------------------------
let arr: integer[] = [1, 2, 3];
let mezcla = [1, "dos"];             // [35] elementos incompatibles
let malIndice: integer = arr["i"];   // [36] índice no entero
let noArreglo: integer = n[0];       // [37] indexar algo que no es arreglo
let flotantes: float[] = arr;        // [38] arreglos invariantes

// ---------- Generales ---------------------------------------
function muerto(): integer {
  return 1;
  print("nunca");                    // [39] código muerto
}
function multiplicaFuncion(): integer { return sumar * 2; } // [40] multiplicar una función
const CONSTANTE: integer = 1;
CONSTANTE = 2;                       // [41] reasignar una constante
function sinRetornar(): integer { print("nada"); }  // [42] no retorna en todos los caminos
