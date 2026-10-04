func fact(n):
    if n > 1 goto L2
    return 1
L2:
    $t1 = n - 1
    param $t1
    $t1 = call fact, 1
    $t1 = n * $t1
    return $t1
endfunc
func __main():
    param 5
    $t1 = call fact, 1
    print $t1
endfunc
