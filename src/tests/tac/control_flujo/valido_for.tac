func __main():
    total = 0
    i = 0
L1:
    if i >= 5 goto L4
    $t1 = total + i
    total = $t1
    $t1 = i + 1
    i = $t1
    goto L1
L4:
    j = 0
    j = 10
L5:
    if j <= 0 goto L8
    print j
    $t1 = j - 2
    j = $t1
    goto L5
L8:
    k = 0
L9:
    if k >= 3 goto L12
    $t1 = k + 1
    k = $t1
    goto L9
L12:
    v = 0
L13:
    if v >= 4 goto L16
    print v
    $t1 = v + 1
    v = $t1
    goto L13
L16:
    w = 0
L17:
    if w >= 2 goto L20
    z = 0
L21:
    if z >= 2 goto L24
    $t1 = w * 2
    $t1 = $t1 + z
    print $t1
    $t1 = z + 1
    z = $t1
    goto L21
L24:
    $t1 = w + 1
    w = $t1
    goto L17
L20:
endfunc
