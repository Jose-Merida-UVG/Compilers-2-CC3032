class Animal:
func Animal.__init_fields(this):
    this.nombre = "sin nombre"
    return
endfunc
func Animal.describir(this):
    $t1 = this.nombre
    $t1 = "animal: " + $t1
    return $t1
endfunc
endclass
class Gato : Animal:
func Gato.__init_fields(this):
    param this
    call Animal.__init_fields, 1
    return
endfunc
func Gato.maullar(this):
    return "miau"
endfunc
endclass
func __main():
    $t1 = new Gato
    param $t1
    call Gato.__init_fields, 1
    g = $t1
    param g
    $t1 = call Animal.describir, 1
    print $t1
    param g
    $t1 = call Gato.maullar, 1
    print $t1
endfunc
