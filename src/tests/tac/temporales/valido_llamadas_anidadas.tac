func f(x):
    $t1 = x + 1
    return $t1
endfunc
func g(a, b):
    $t1 = a * b
    return $t1
endfunc
func __main():
    param 1
    $t1 = call f, 1
    param $t1
    $t1 = call f, 1
    param $t1
    $t1 = call f, 1
    print $t1
    param 1
    $t1 = call f, 1
    $t1 = $t1 + 2
    param 3
    $t2 = call f, 1
    $t2 = $t2 * 4
    param $t1
    param $t2
    $t1 = call g, 2
    print $t1
    param 1
    param 2
    $t1 = call g, 2
    param 3
    param 4
    $t2 = call g, 2
    param $t1
    param $t2
    $t1 = call g, 2
    param 5
    $t2 = call f, 1
    $t1 = $t1 + $t2
    print $t1
endfunc
