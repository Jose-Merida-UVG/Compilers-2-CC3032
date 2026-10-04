class Cuenta:
func Cuenta.__init_fields(this):
    this.saldo = 0
    this.tasa = 0.0
    return
endfunc
func Cuenta.constructor(this, inicial):
    this.saldo = inicial
    return
endfunc
func Cuenta.depositar(this, monto):
    if monto <= 0 goto L2
    $t1 = this.saldo
    $t1 = $t1 + monto
    this.saldo = $t1
L2:
    return
endfunc
func Cuenta.ajustar(this):
    this.tasa = 2.0
    return
endfunc
func Cuenta.ver(this):
    $t1 = this.saldo
    return $t1
endfunc
endclass
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
    call Cuenta.depositar, 2
    param c
    $t1 = call Cuenta.ver, 1
    print $t1
endfunc
