class Calc:
func Calc.__init_fields(this):
    return
endfunc
func Calc.fact(this, n):
    if n > 1 goto L2
    return 1
L2:
    $t1 = n - 1
    param this
    param $t1
    $t1 = call Calc.fact, 2
    $t1 = n * $t1
    return $t1
endfunc
func Calc.pot(this, b, e):
    if e != 0 goto L4
    return 1
L4:
    $t1 = e - 1
    param this
    param b
    param $t1
    $t1 = call Calc.pot, 3
    $t1 = b * $t1
    return $t1
endfunc
endclass
func __main():
    $t1 = new Calc
    param $t1
    call Calc.__init_fields, 1
    c = $t1
    param c
    param 5
    $t1 = call Calc.fact, 2
    print $t1
    param c
    param 2
    param 3
    $t1 = call Calc.pot, 3
    print $t1
endfunc
