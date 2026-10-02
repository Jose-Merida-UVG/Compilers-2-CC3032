func __main():
    a = 1
    b = 2
    f = 1.5
    $t1 = a < b
    c1 = $t1
    $t1 = a <= b
    c2 = $t1
    $t1 = a > b
    c3 = $t1
    $t1 = a >= b
    c4 = $t1
    $t1 = a == b
    c5 = $t1
    $t1 = a != b
    c6 = $t1
    $t1 = a + 1
    $t2 = b * 2
    $t1 = $t1 < $t2
    c7 = $t1
    $t1 = itof a
    $t1 = $t1 < f
    c8 = $t1
    $t1 = f >= 2.0
    c9 = $t1
    $t1 = "x" == "y"
    s1 = $t1
    t1 = true
    $t1 = t1 != false
    t2 = $t1
    print c1
endfunc
