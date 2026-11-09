// La función puede tener sus propios bucles y switch aunque esté dentro de un bucle.
let i: integer = 0;
while (i < 2) {
  function h(x: integer): integer {
    let k: integer = 0;
    while (k < 3) {
      k = k + 1;
      if (k == 2) { break; }
    }
    switch (x) { case 1: return 10; case 2: break; }
    return k;
  }
  print(h(i));
  i = i + 1;
}
