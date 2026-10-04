func __main():
    a = 1
    b = 2
    c = 3
    d = 4
    e = 5
    f = 6
    $t1 = a + b
    $t1 = $t1 + c
    $t1 = $t1 + d
    $t1 = $t1 + e
    $t1 = $t1 + f
    suma = $t1
    $t1 = a + b
    $t2 = c - d
    $t1 = $t1 * $t2
    $t2 = e + f
    $t3 = a - b
    $t2 = $t2 * $t3
    $t1 = $t1 / $t2
    mezcla = $t1
    $t1 = e + f
    $t1 = d * $t1
    $t1 = c + $t1
    $t1 = b * $t1
    $t1 = a + $t1
    profunda = $t1
    $t1 = suma + mezcla
    $t1 = $t1 + profunda
    print $t1
endfunc
