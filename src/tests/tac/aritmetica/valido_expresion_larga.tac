func __main():
    a = 1
    b = 2
    c = 3
    d = 4
    e = 5
    $t1 = a + b
    $t2 = c + d
    $t1 = $t1 * $t2
    $t2 = e - a
    $t3 = b + c
    $t2 = $t2 * $t3
    $t1 = $t1 - $t2
    $t2 = a * b
    $t2 = $t2 * c
    $t2 = $t2 * d
    $t2 = $t2 * e
    $t1 = $t1 + $t2
    r = $t1
    print r
    $t1 = c * d
    $t1 = b + $t1
    a = $t1
    $t1 = a + b
    $t2 = c + d
    $t1 = $t1 * $t2
    b = $t1
endfunc
