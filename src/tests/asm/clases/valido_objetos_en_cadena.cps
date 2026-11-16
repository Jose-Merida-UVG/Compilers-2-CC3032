class Nodo {
    var valor: integer;
    var siguiente: Nodo;
    function constructor(v: integer) { this.valor = v; this.siguiente = null; }
    function obtener(): integer { return this.valor; }
}
let a = new Nodo(1);
let b = new Nodo(2);
a.siguiente = b;
print(a.siguiente.valor);
print(a.siguiente.obtener());
a.siguiente.valor = 5;
print(new Nodo(9).obtener());
