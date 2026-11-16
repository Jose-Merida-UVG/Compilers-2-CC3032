// Regresión: un argumento calculado (temporal) no debe perderse cuando cargar otro argumento le quita el registro.
function g5(p: integer, q: integer, r: integer, s: integer, t: integer, u: integer, v: integer, w: integer): integer { return p + q + r + s + t + u + v + w; }
let a: integer = 1; let b: integer = 2; let c: integer = 3; let d: integer = 4; let e: integer = 5;
let f: integer = 6; let g: integer = 7; let h: integer = 8; let i: integer = 9; let j: integer = 10;
print(g5(0, 0, 0, 0, h + i, 0, 0, 0));
print(g5(0, 0, 0, g, h + i, 0, 0, 0));
print(g5(0, 0, e - f, 0, h + i, 0, 0, 0));
print(g5(0, c * d, 0, 0, h + i, 0, 0, 0));
print(g5(a + b, 0, 0, 0, h + i, 0, 0, 0));
print(g5(a + b, c * d, e - f, g, h + i, j, 0, 0));
