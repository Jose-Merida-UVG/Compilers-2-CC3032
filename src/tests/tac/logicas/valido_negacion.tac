func __main():
    a = true
    x = 1
    y = 2
    $t1 = ! a
    n1 = $t1
    $t1 = ! a
    $t1 = ! $t1
    n2 = $t1
    n3 = false
    n4 = true
    $t1 = x < y
    $t1 = ! $t1
    n5 = $t1
    ifFalse a goto L2
    ifFalse n1 goto L2
    $t1 = true
    goto L3
L2:
    $t1 = false
L3:
    $t1 = ! $t1
    n6 = $t1
    ifFalse a goto L5
    if n1 goto L6
L5:
    $t1 = true
    goto L7
L6:
    $t1 = false
L7:
    n7 = $t1
    $t1 = ! a
    print $t1
endfunc
