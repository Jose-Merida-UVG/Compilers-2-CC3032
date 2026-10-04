class Punto:
func Punto.__init_fields(this):
    this.x = 0
    this.y = 0
    return
endfunc
func Punto.constructor(this, a, b):
    this.x = a
    this.y = b
    return
endfunc
endclass
func __main():
    $t1 = new Punto
    param $t1
    call Punto.__init_fields, 1
    param $t1
    param 3
    param 4
    call Punto.constructor, 3
    p = $t1
    $t1 = p.x
    print $t1
    $t1 = p.x
    $t1 = $t1 + 1
    p.y = $t1
    $t1 = p.y
    print $t1
endfunc
