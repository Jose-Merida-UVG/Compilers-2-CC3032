class A:
func A.__init_fields(this):
    this.a = 1
    return
endfunc
func A.quien(this):
    return "A"
endfunc
func A.soloA(this):
    $t1 = this.a
    return $t1
endfunc
endclass
class B : A:
func B.__init_fields(this):
    param this
    call A.__init_fields, 1
    this.b = 2
    return
endfunc
func B.quien(this):
    return "B"
endfunc
endclass
class C : B:
func C.__init_fields(this):
    param this
    call B.__init_fields, 1
    this.c = 3
    return
endfunc
func C.suma(this):
    $t1 = this.a
    $t2 = this.b
    $t1 = $t1 + $t2
    $t2 = this.c
    $t1 = $t1 + $t2
    return $t1
endfunc
endclass
func __main():
    $t1 = new C
    param $t1
    call C.__init_fields, 1
    x = $t1
    param x
    $t1 = call B.quien, 1
    print $t1
    param x
    $t1 = call A.soloA, 1
    print $t1
    param x
    $t1 = call C.suma, 1
    print $t1
endfunc
