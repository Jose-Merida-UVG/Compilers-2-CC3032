func __main():
    x = 1
    try L1
    if x <= 0 goto L4
    print "positivo"
    goto L5
L4:
    print "no positivo"
L5:
    $t1 = newarray 2
    $t1[0] = 1
    $t1[1] = 2
    $t2 = len $t1
    $t3 = 0
L6:
    if $t3 >= $t2 goto L8
    v = $t1[$t3]
    print v
    $t3 = $t3 + 1
    goto L6
L8:
    endtry
    goto L2
L1:
    catch e
    x = 0
    $t1 = "error: " + e
    print $t1
L2:
endfunc
