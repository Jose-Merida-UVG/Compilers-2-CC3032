class Nodo {
    var valor: integer;
    var siguiente: Nodo;
    function constructor(v: integer) { this.valor = v; this.siguiente = null; }
}
let n = new Nodo(1);
try {
    print(n.siguiente.valor);
} catch (e) {
    print(e);
}
