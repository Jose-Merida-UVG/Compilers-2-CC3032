func __main():
    $t1 = newarray 3
    $t1[0] = 1
    $t1[1] = 2
    $t1[2] = 3
    a = $t1
    try L1
    $t1 = a[100]
    peligro = $t1
    print peligro
    endtry
    goto L2
L1:
    catch err
    $t1 = "Error atrapado: " + err
    print $t1
L2:
    print "fin"
endfunc
