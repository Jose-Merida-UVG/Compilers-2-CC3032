func seguro(a, i):
    try L1
    $t1 = a[i]
    endtry
    return $t1
L1:
    catch e
    return 0
    return
endfunc
func __main():
    $t1 = newarray 3
    $t1[0] = 1
    $t1[1] = 2
    $t1[2] = 3
    param $t1
    param 1
    $t1 = call seguro, 2
    print $t1
endfunc
