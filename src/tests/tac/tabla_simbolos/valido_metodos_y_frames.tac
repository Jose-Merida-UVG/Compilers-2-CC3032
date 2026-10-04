class Cuenta:
func Cuenta.__init_fields(this):
    this.saldo = 0
    return
endfunc
func Cuenta.constructor(this, inicial):
    this.saldo = inicial
    return
endfunc
func Cuenta.depositar(this, monto):
    $t1 = this.saldo
    $t1 = $t1 + monto
    nuevo = $t1
    this.saldo = nuevo
    return nuevo
endfunc
endclass
func total(c, extra):
    param c
    param extra
    $t1 = call Cuenta.depositar, 2
    t = $t1
    $t1 = t * 2
    return $t1
endfunc
func __main():
    $t1 = new Cuenta
    param $t1
    call Cuenta.__init_fields, 1
    param $t1
    param 10
    call Cuenta.constructor, 2
    c = $t1
    param c
    param 5
    $t1 = call total, 2
    print $t1
endfunc
