let x: integer = 5;
const name: string = "compiscript";

function add(a: integer, b: integer): integer {
  return a + b;
}

if (x > 0) {
  print(add(x, 2));
} else {
  print(0);
}

while (x > 0) {
  x = x - 1;
}
