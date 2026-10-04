function f(x: integer): integer { return x + 1; }
function g(a: integer, b: integer): integer { return a * b; }
print(f(f(f(1))));
print(g(f(1) + 2, f(3) * 4));
print(g(g(1, 2), g(3, 4)) + f(5));
