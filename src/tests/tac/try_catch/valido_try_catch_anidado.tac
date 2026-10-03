func __main():
    try L1
    print "externo"
    try L3
    print "interno"
    endtry
    goto L4
L3:
    catch e1
    print e1
L4:
    endtry
    goto L2
L1:
    catch e2
    $t1 = "fallo " + e2
    print $t1
L2:
endfunc
