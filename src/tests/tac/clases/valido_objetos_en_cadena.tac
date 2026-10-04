class Nodo:
func Nodo.__init_fields(this):
    return
endfunc
func Nodo.constructor(this, v):
    this.valor = v
    this.siguiente = null
    return
endfunc
func Nodo.obtener(this):
    $t1 = this.valor
    return $t1
endfunc
endclass
func __main():
    $t1 = new Nodo
    param $t1
    call Nodo.__init_fields, 1
    param $t1
    param 1
    call Nodo.constructor, 2
    a = $t1
    $t1 = new Nodo
    param $t1
    call Nodo.__init_fields, 1
    param $t1
    param 2
    call Nodo.constructor, 2
    b = $t1
    a.siguiente = b
    $t1 = a.siguiente
    $t1 = $t1.valor
    print $t1
    $t1 = a.siguiente
    param $t1
    $t1 = call Nodo.obtener, 1
    print $t1
    $t1 = a.siguiente
    $t1.valor = 5
    $t1 = new Nodo
    param $t1
    call Nodo.__init_fields, 1
    param $t1
    param 9
    call Nodo.constructor, 2
    param $t1
    $t1 = call Nodo.obtener, 1
    print $t1
endfunc
