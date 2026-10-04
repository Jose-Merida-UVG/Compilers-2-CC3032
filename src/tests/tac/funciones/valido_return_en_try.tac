func primero(a):
    try L1
    $t1 = a[0]
    endtry
    return $t1
L1:
    catch e
    print e
    return 0
endfunc
func __main():
    $t1 = newarray 2
    $t1[0] = 7
    $t1[1] = 8
    xs = $t1
    param xs
    $t1 = call primero, 1
    print $t1
endfunc
