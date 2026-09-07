// Sistema de tipos — un error por línea marcada con [n].
let t1: integer = "texto";           // [1] asignación: tipo no coincide
let t2: integer = 1 + true;          // [2] aritmética con boolean
let t3: boolean = 1 && true;         // [3] lógica con integer
let t4: boolean = "a" < 3;           // [4] comparación incompatible
let t5: boolean = 5 == "cinco";      // [5] igualdad incompatible
let t6: integer = -"x";              // [6] unario '-' sobre string
let t7: boolean = !5;                // [7] unario '!' sobre integer
let t8: integer = 5 ? 1 : 2;         // [8] condición de ternario no boolean
const K: integer = 1;
K = 2;                               // [9] reasignar una constante
