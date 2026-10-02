func __main():
    a = 2
    b = 3
    c = 4
    d = 5
    $t1 = b * c
    $t1 = a + $t1
    r1 = $t1
    $t1 = a * b
    $t2 = c * d
    $t1 = $t1 + $t2
    r2 = $t1
    $t1 = a + b
    $t2 = c - d
    $t1 = $t1 * $t2
    r3 = $t1
    $t1 = a + b
    $t1 = $t1 + c
    $t1 = $t1 + d
    r4 = $t1
    $t1 = a - b
    $t1 = $t1 - c
    r5 = $t1
    $t1 = a * b
    $t1 = $t1 / c
    $t1 = $t1 % d
    r6 = $t1
    $t1 = r1 + r2
    $t1 = $t1 + r3
    print $t1
endfunc
