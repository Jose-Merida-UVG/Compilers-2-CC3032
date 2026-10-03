let x: integer = 1;
switch (x) {
    case 1:
        print("uno");
    case 2:
        print("dos");
    default:
        print("otro");
}
let dia: integer = 3;
switch (dia) {
    case 1:
        print("lunes");
    case 2:
        print("martes");
}
let nombre: string = "b";
switch (nombre) {
    case "a":
        print("A");
    case "b":
        print("B");
}
let suma: integer = 0;
switch (suma + 1) {
    case 0:
        suma = 10;
    default:
        suma = suma + 1;
}
