class Contador:
func Contador.__init_fields(this):
    this.n = 0
    return
endfunc
func Contador.incrementar(this):
    $t1 = this.n
    $t1 = $t1 + 1
    this.n = $t1
    return
endfunc
func Contador.valor(this):
    $t1 = this.n
    return $t1
endfunc
func Contador.sumar(this, k):
    param this
    call Contador.incrementar, 1
    param this
    $t1 = call Contador.valor, 1
    $t1 = $t1 + k
    return $t1
endfunc
endclass
func __main():
    $t1 = new Contador
    param $t1
    call Contador.__init_fields, 1
    c = $t1
    param c
    call Contador.incrementar, 1
    param c
    $t1 = call Contador.valor, 1
    print $t1
    param c
    param 10
    $t1 = call Contador.sumar, 2
    print $t1
endfunc
