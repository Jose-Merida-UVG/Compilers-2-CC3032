class Cuenta {
    var saldo: integer = 0;
    var tasa: float = 0.0;
    function constructor(inicial: integer) { saldo = inicial; }
    function depositar(monto: integer) {
        if (monto > 0) { saldo = saldo + monto; }
    }
    function ajustar() { tasa = 2; }
    function ver(): integer { return saldo; }
}
let c = new Cuenta(10);
c.depositar(5);
print(c.ver());
