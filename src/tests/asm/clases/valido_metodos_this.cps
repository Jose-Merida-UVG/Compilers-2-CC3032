class Contador {
    var n: integer = 0;
    function incrementar() { this.n = this.n + 1; }
    function valor(): integer { return this.n; }
    function sumar(k: integer): integer { this.incrementar(); return this.valor() + k; }
}
let c = new Contador();
c.incrementar();
print(c.valor());
print(c.sumar(10));
