class Animal:
func Animal.__init_fields(this):
    return
endfunc
func Animal.hablar(this):
    return "..."
endfunc
endclass
class Perro : Animal:
func Perro.__init_fields(this):
    param this
    call Animal.__init_fields, 1
    return
endfunc
func Perro.hablar(this):
    return "guau"
endfunc
endclass
func __main():
    $t1 = new Animal
    param $t1
    call Animal.__init_fields, 1
    a = $t1
    $t1 = new Perro
    param $t1
    call Perro.__init_fields, 1
    p = $t1
    param a
    $t1 = call Animal.hablar, 1
    print $t1
    param p
    $t1 = call Perro.hablar, 1
    print $t1
endfunc
