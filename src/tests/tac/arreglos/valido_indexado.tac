func __main():
    $t1 = newarray 4
    $t1[0] = 10
    $t1[1] = 20
    $t1[2] = 30
    $t1[3] = 40
    a = $t1
    i = 1
    $t1 = a[0]
    p = $t1
    $t1 = i + 1
    $t1 = a[$t1]
    q = $t1
    $t1 = a[0]
    $t2 = a[1]
    $t3 = a[2]
    $t2 = $t2 * $t3
    $t1 = $t1 + $t2
    suma = $t1
    a[0] = 99
    $t1 = a[i]
    $t1 = $t1 + 1
    a[i] = $t1
    $t1 = i + 1
    $t2 = a[i]
    $t2 = $t2 * 2
    a[$t1] = $t2
    $t1 = a[0]
    $t1 = $t1 + 5
    a[3] = $t1
    $t1 = a[i]
    print $t1
    $t1 = p + q
    $t1 = $t1 + suma
    print $t1
endfunc
