func __main():
    n = 0
L1:
    $t1 = n + 1
    n = $t1
    if n < 5 goto L6
    goto L4
L6:
    goto L1
L4:
    print n
endfunc
