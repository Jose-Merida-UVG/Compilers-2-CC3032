func primero_par(a):
    $t1 = len a
    $t2 = 0
L1:
    if $t2 >= $t1 goto L3
    x = a[$t2]
    try L4
    $t3 = x % 2
    if $t3 != 0 goto L7
    endtry
    return x
L7:
    endtry
    goto L5
L4:
    catch e
    print e
L5:
    $t2 = $t2 + 1
    goto L1
L3:
    return -1
endfunc
func __main():
    $t1 = newarray 4
    $t1[0] = 1
    $t1[1] = 3
    $t1[2] = 4
    $t1[3] = 6
    param $t1
    $t1 = call primero_par, 1
    print $t1
endfunc
