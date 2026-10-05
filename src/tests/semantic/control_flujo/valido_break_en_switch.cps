// `break` también es válido dentro de un switch (sale del switch), con o sin bucle.
let x: integer = 1;
switch (x) {
  case 1:
    print("uno");
    break;
  case 2:
    print("dos");
  default:
    print("otro");
}
let i: integer = 0;
while (i < 5) {
  i = i + 1;
  switch (i % 3) {
    case 0:
      continue;
    case 1:
      break;
    default:
      print(i);
  }
}
