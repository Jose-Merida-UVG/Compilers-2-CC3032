// Demo — sentencias de control: if/else, while, do-while, for, foreach, switch y break/continue.
// Correr con ▶ y mirar la pestaña "tac" (las condiciones son saltos; una condición se invierte para no emitir goto).

// --- if / else, y un if dentro del else (la gramática no tiene "else if")
let x: integer = 7;
if (x < 5) {
    print("chico");
} else {
    if (x < 10) {
        print("mediano");
    } else {
        print("grande");
    }
}

// --- while, con continue y break
let i: integer = 0;
while (true) {
    i = i + 1;
    if (i == 3) {
        continue;       // vuelve al inicio del while (while (true) no tiene condición que evaluar)
    }
    if (i > 5) {
        break;          // sale del while
    }
    print(i);
}

// --- do-while: el cuerpo corre al menos una vez
let n: integer = 3;
do {
    n = n - 1;
    if (n == 1) {
        continue;       // salta a la condición del do-while
    }
    print(n);
} while (n > 0);

// --- for, con continue (salta al update) y break
for (let k: integer = 0; k < 10; k = k + 1) {
    if (k % 2 == 0) {
        continue;
    }
    if (k > 7) {
        break;
    }
    print(k);
}

// --- foreach, con continue y break
let notas: integer[] = [90, 50, 100, 70];
foreach (nota in notas) {
    if (nota < 60) {
        continue;
    }
    if (nota == 100) {
        break;
    }
    print(nota);
}

// --- switch: sin break los casos caen en el siguiente (como en TypeScript)
let dia: integer = 1;
switch (dia) {
    case 1:
        print("lunes");
    case 2:
        print("martes");    // dia = 1 imprime lunes y martes
    default:
        print("otro");      // ...y también otro
}

// --- switch con break: sale del switch; sin default, sin coincidencia no hace nada
let op: integer = 2;
switch (op) {
    case 1:
        print("uno");
        break;
    case 2:
        print("dos");
        break;
}

// --- switch sobre strings y sobre una expresión
let nombre: string = "b";
switch (nombre) {
    case "a":
        print("A");
        break;
    case "b":
        print("B");
        break;
    default:
        print("?");
}
let suma: integer = 0;
switch (suma + 1) {
    case 0:
        suma = 10;
        break;
    default:
        suma = suma + 1;
}

// --- switch dentro de un bucle: break sale del switch, continue sigue con el bucle
let j: integer = 0;
while (j < 6) {
    j = j + 1;
    switch (j % 3) {
        case 0:
            continue;       // al while, no al switch
        case 1:
            break;          // sale del switch; sigue con print(j)
        default:
            print("resto 2");
    }
    print(j);
}

// --- bucles anidados: break solo sale del bucle más interno
let a: integer = 0;
while (a < 3) {
    let b: integer = 0;
    while (b < 3) {
        if (b == 1) {
            break;
        }
        b = b + 1;
    }
    a = a + 1;
}
