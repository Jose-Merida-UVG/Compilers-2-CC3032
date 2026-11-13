// Demo — sentencias de control con errores: no se genera TAC.
let a: integer = 1;

// break y continue solo valen dentro de un bucle (break también en un switch)
if (a == 1) {
    break;
}
continue;

// continue no vale en un switch que no está dentro de un bucle
switch (a) {
    case 1:
        continue;
}

// break dentro de una función que no está en un bucle ni en un switch
function f() {
    break;
}

// las condiciones deben ser boolean
if (a) {
    print("no es boolean");
}
while (a + 1) {
    print("tampoco");
}

// el tipo de un case debe ser compatible con el del switch
switch (a) {
    case "uno":
        print("string contra integer");
}
