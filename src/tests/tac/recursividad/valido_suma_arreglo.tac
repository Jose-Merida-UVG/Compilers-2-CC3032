func sumar(a, i, n):
    if i < n goto L2
    return 0
L2:
    $t1 = a[i]
    $t2 = i + 1
    param a
    param $t2
    param n
    $t2 = call sumar, 3
    $t1 = $t1 + $t2
    return $t1
endfunc
func __main():
    $t1 = newarray 4
    $t1[0] = 1
    $t1[1] = 2
    $t1[2] = 3
    $t1[3] = 4
    xs = $t1
    param xs
    param 0
    param 4
    $t1 = call sumar, 3
    print $t1
endfunc
