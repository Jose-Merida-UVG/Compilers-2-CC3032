function doble(x: integer): integer { return x * 2; }
function suma(a: integer, b: integer): integer { return a + b; }
print(suma(doble(2), doble(3)));
print(doble(doble(doble(1))));
print(suma(suma(1, 2), suma(3, 4)));
