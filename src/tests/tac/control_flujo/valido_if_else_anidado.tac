func __main():
    x = 15
    if x >= 10 goto L2
    print "chico"
    goto L3
L2:
    if x >= 20 goto L5
    print "mediano"
    goto L6
L5:
    print "grande"
L6:
L3:
    if x <= 0 goto L8
    $t1 = x % 2
    if $t1 != 0 goto L10
    print "par"
    goto L11
L10:
    print "impar"
L11:
L8:
endfunc
