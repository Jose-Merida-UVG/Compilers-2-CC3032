// Dos 'case' declarando el mismo nombre colisionan (comparten un scope).
let dia: integer = 1;
switch (dia) {
  case 1:
    let mensaje: integer = 10;
    print(mensaje);
  case 2:
    let mensaje: integer = 20;
    print(mensaje);
}
