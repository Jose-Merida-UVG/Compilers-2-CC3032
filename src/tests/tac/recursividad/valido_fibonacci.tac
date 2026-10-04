func fib(n):
    if n >= 2 goto L2
    return n
L2:
    $t1 = n - 1
    param $t1
    $t1 = call fib, 1
    $t2 = n - 2
    param $t2
    $t2 = call fib, 1
    $t1 = $t1 + $t2
    return $t1
endfunc
func __main():
    param 7
    $t1 = call fib, 1
    print $t1
endfunc
