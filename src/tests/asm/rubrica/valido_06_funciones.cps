function suma(a: integer, b: integer, c: integer, d: integer, e: integer): integer { return a + b + c + d + e; }
function sinRet(x: integer) { print(x); }
function conFloat(x: float, y: integer): float { return x * y; }
function saludo(n: string, veces: integer): string { let r: string = ""; for (let i: integer = 0; i < veces; i = i + 1) { r = r + n; } return r; }
function esPar(n: integer): boolean { return n % 2 == 0; }
print(suma(1, 2, 3, 4, 5)); sinRet(suma(1,1,1,1,1) * suma(2,2,2,2,2));
print(conFloat(2.5, 4)); print(saludo("ab", 3)); print(esPar(4) && !esPar(5));
print(suma(suma(1,1,1,1,1), 1, 1, 1, suma(0,0,0,0,1)));
function ext(n: integer): integer { function dentro(m: integer): integer { return m + n; } return dentro(n * 2); }
print(ext(5));
