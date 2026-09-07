// Arreglos — un error por línea marcada con [n].
let arr: integer[] = [1, 2, 3];
let n: integer = 3;
let mezcla = [1, "dos"];             // [1] elementos incompatibles
let malIndice: integer = arr["i"];   // [2] índice no entero
let noArreglo: integer = n[0];       // [3] indexar algo que no es arreglo
let flotantes: float[] = arr;        // [4] arreglos invariantes
let matriz: float[][] = [[1, 2]];    // [5] invariancia anidada
foreach (x in n) { print(x); }       // [6] foreach sobre algo que no es arreglo
