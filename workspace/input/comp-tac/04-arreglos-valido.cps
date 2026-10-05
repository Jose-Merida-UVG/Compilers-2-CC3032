// Demo — arreglos: literales, indexado y multidimensionales. Correr con ▶ y mirar la pestaña "tac".
let m = [[1, 2], [3, 4]];
let i: integer = 0;
let j: integer = 1;
let v = m[i][j];
m[0][1] = 7;
m[i][j] = m[j][i] + 1;
let fila = m[1];
fila[0] = 100;
let cubo: integer[][][] = [[[1]], [[2], [3]]];
print(cubo[1][0][0]);
print(m[1][1] + v);
