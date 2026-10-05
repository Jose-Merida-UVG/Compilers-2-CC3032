// Demo — tabla de símbolos con datos para código objeto. Correr con ▶ y
// mirar la pestaña "symbols": size/offset/address/label por símbolo,
// frame por función (registro de activación) y layout por clase.
let a: integer = 1;               // gp+0
let ok: boolean = true;           // gp+4 (1 byte)
let f: float = 2.5;               // gp+8 (se alinea a 4)
const MAX: integer = 10;

class Animal {
    var nombre: string = "animal";
    var patas: integer = 4;
    function hablar(): string { return "..."; }
}
class Perro : Animal {            // hereda nombre y patas en los mismos offsets
    var vivo: boolean = true;
    function hablar(): string { return "guau"; }   // overrides Animal.hablar
}

function mezcla(a: integer, b: boolean, c: float): integer {
    let x: integer = a;           // fp-4
    let activo: boolean = b;      // fp-5
    {
        let z: integer = x * 2 + a * 3;   // dos temporales vivos a la vez
        x = z;
    }
    if (activo) { return x; }
    return mezcla(x, false, c);
}

let p = new Perro();
print(p.hablar());
print(mezcla(1, true, 2.0));
