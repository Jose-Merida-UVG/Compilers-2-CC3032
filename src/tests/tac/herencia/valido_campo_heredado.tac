class Animal:
func Animal.__init_fields(this):
    return
endfunc
func Animal.constructor(this, n):
    this.nombre = n
    return
endfunc
endclass
class Perro : Animal:
func Perro.__init_fields(this):
    param this
    call Animal.__init_fields, 1
    this.raza = "criollo"
    return
endfunc
func Perro.info(this):
    $t1 = this.nombre
    $t1 = $t1 + " ("
    $t2 = this.raza
    $t1 = $t1 + $t2
    $t1 = $t1 + ")"
    return $t1
endfunc
endclass
func __main():
    $t1 = new Perro
    param $t1
    call Perro.__init_fields, 1
    param $t1
    param "rex"
    call Animal.constructor, 2
    p = $t1
    p.nombre = "max"
    param p
    $t1 = call Perro.info, 1
    print $t1
endfunc
