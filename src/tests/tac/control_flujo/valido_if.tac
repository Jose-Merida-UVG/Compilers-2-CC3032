func __main():
    a = 5
    b = 7
    ok = true
    if a >= b goto L2
    print "menor"
L2:
    ifFalse ok goto L4
    $t1 = a + 1
    a = $t1
L4:
    if a != b goto L6
    print "igual"
    goto L7
L6:
    print "distinto"
L7:
    if ok goto L9
    print "no"
L9:
    print "siempre"
endfunc
