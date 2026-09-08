// Una variable declarada dentro de un 'switch' no sobrevive a su cierre.
let dia: integer = 1;
switch (dia) {
  case 1:
    let mensaje: integer = 10;
    print(mensaje);
}
print(mensaje);
