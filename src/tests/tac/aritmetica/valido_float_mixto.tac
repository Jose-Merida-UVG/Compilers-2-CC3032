func __main():
    i = 3
    f = 2.5
    $t1 = itof i
    $t1 = $t1 + f
    a = $t1
    $t1 = itof i
    $t1 = f * $t1
    b = $t1
    $t1 = f - 1.0
    c = $t1
    $t1 = itof i
    $t1 = $t1 * f
    $t1 = 1.0 + $t1
    d = $t1
    $t1 = i * 2
    $t1 = itof $t1
    e = $t1
    print a
    $t1 = b + c
    $t1 = $t1 + d
    $t1 = $t1 + e
    print $t1
endfunc
