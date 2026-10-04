func __main():
    i = 0
L1:
    print i
    $t1 = i + 1
    i = $t1
    if i < 3 goto L1
    n = 10
L4:
    $t1 = n - 1
    n = $t1
    if n != 5 goto L8
    goto L5
L8:
    print n
L5:
    if n > 0 goto L4
endfunc
