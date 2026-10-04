func doble(x):
    $t1 = x * 2
    return $t1
endfunc
func suma(a, b):
    $t1 = a + b
    return $t1
endfunc
func __main():
    param 2
    $t1 = call doble, 1
    param 3
    $t2 = call doble, 1
    param $t1
    param $t2
    $t1 = call suma, 2
    print $t1
    param 1
    $t1 = call doble, 1
    param $t1
    $t1 = call doble, 1
    param $t1
    $t1 = call doble, 1
    print $t1
    param 1
    param 2
    $t1 = call suma, 2
    param 3
    param 4
    $t2 = call suma, 2
    param $t1
    param $t2
    $t1 = call suma, 2
    print $t1
endfunc
