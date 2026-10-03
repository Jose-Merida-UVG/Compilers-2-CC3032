func __main():
    i = 0
L1:
    $t1 = i + 1
    i = $t1
    if i != 3 goto L5
    goto L1
L5:
    if i <= 6 goto L7
    goto L3
L7:
    print i
    goto L1
L3:
    k = 0
L8:
    if k >= 10 goto L11
    $t1 = k % 2
    if $t1 != 0 goto L13
    goto L10
L13:
    if k <= 7 goto L15
    goto L11
L15:
    print k
L10:
    $t1 = k + 1
    k = $t1
    goto L8
L11:
    a = 0
L16:
    if a >= 3 goto L18
    b = 0
L19:
    if b >= 3 goto L21
    if b != 1 goto L23
    goto L21
L23:
    $t1 = b + 1
    b = $t1
    goto L19
L21:
    $t1 = a + 1
    a = $t1
    goto L16
L18:
endfunc
