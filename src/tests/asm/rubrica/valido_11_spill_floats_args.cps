let a: integer = 1; let b: integer = 2; let c: integer = 3; let d: integer = 4; let e: integer = 5;
let f: integer = 6; let g: integer = 7; let h: integer = 8; let i: integer = 9; let j: integer = 10;
let k: integer = 11; let l: integer = 12;
print(((a + b) * (c + d) + (e + f) * (g + h)) * ((i + j) * (k + l) - (a * b * c * d)) + (((a+b)+(c+d))+((e+f)+(g+h)))*(((i+j)+(k+l))+((a+c)+(b+d))));
let x: float = 1.5; let y: float = 2.5; let z: float = 0.5; let w: float = 4.0;
print(((x + y) * (z + w) + (x * y) * (z * w)) - ((x - z) * (y - w)) + ((x+y)+(z+w)) * ((x*2.0)+(y*2.0)));
function g5(p: integer, q: integer, r: integer, s: integer, t: integer, u: integer, v: integer, w: integer): integer { return p - q + r - s + t - u + v - w; }
print(g5(a + b, c * d, e - f, g, h + i, j, k * 2, l) + g5(1,2,3,4,5,6,7,8) * (a + g5(8,7,6,5,4,3,2,1)));
