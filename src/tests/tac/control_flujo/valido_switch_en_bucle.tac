func __main():
    i = 0
L1:
    if i >= 6 goto L3
    $t1 = i % 3
    if $t1 == 0 goto L4
    if $t1 == 1 goto L5
    goto L6
L4:
    $t1 = i + 1
    i = $t1
    goto L1
L5:
    if i <= 3 goto L9
    goto L3
L9:
L6:
    print i
    $t1 = i + 1
    i = $t1
    goto L1
L3:
endfunc
