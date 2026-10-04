func __main():
    i = 0
L1:
    if i >= 5 goto L3
    $t1 = i + 1
    i = $t1
    try L4
    if i != 2 goto L7
    endtry
    goto L1
L7:
    if i != 4 goto L9
    endtry
    goto L3
L9:
    print i
    endtry
    goto L5
L4:
    catch e
    print e
L5:
    goto L1
L3:
    k = 0
L10:
    if k >= 3 goto L13
    try L14
    print k
    endtry
    goto L15
L14:
    catch err
    print "x"
L15:
    $t1 = k + 1
    k = $t1
    goto L10
L13:
endfunc
