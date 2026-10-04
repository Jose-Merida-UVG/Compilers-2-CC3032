func __main():
    a = 3
    b = 9
    c = false
    if a >= b goto L2
    if b >= 10 goto L2
    print "rango"
L2:
    if a > b goto L4
    ifFalse c goto L5
L4:
    print "o"
    goto L7
L5:
    print "ninguno"
L7:
    if a < b goto L10
    ifFalse c goto L9
L10:
    if c goto L9
    print "mixto"
L9:
L12:
    if a >= b goto L14
    if c goto L14
    $t1 = a + 1
    a = $t1
    goto L12
L14:
endfunc
