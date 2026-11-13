// Demo — clases y objetos: campos con valor inicial, constantes,
// constructor, métodos, this, acceso/asignación de campos y encadenado.
class Punto {
    var x: integer = 0;
    var y: integer = 0;
    function constructor(a: integer, b: integer) { this.x = a; this.y = b; }
    function sumar(): integer { return this.x + this.y; }
}
class Config {
    const VERSION: string = "1.0";
    var factor: float = 2;
}
class Nodo {
    var valor: integer;
    var siguiente: Nodo;
    function constructor(v: integer) { this.valor = v; this.siguiente = null; }
    function obtener(): integer { return this.valor; }
}

let p = new Punto(3, 4);
print(p.x);
p.y = p.x + 1;
print(p.sumar());
let c = new Config();
print(c.VERSION);
let a = new Nodo(1);
let b = new Nodo(2);
a.siguiente = b;
print(a.siguiente.obtener());
a.siguiente.valor = 5;
