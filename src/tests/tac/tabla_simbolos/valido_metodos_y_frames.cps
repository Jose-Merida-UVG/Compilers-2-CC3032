class Cuenta {
    var saldo: integer = 0;
    function constructor(inicial: integer) { this.saldo = inicial; }
    function depositar(monto: integer): integer {
        let nuevo: integer = this.saldo + monto;
        this.saldo = nuevo;
        return nuevo;
    }
}
function total(c: Cuenta, extra: integer): integer {
    let t: integer = c.depositar(extra);
    return t * 2;
}
let c = new Cuenta(10);
print(total(c, 5));
