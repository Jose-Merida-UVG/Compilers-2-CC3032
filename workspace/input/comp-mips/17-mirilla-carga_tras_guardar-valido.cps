// Mirilla — carga_tras_guardar: `sw $r, A` y luego `lw $r, A` -> se quita el `lw`.
// Se guarda un campo y se vuelve a leer enseguida.
class Cuenta {
    var saldo: integer = 100;
    function depositar(m: integer): integer {
        this.saldo = this.saldo + m;
        return this.saldo;
    }
}
let c: Cuenta = new Cuenta();
print(c.depositar(5));
