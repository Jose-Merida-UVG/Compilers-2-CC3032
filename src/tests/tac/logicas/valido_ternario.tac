func __main():
    x = 3
    y = 8
    a = true
    b = false
    if x <= y goto L2
    $t1 = x
    goto L3
L2:
    $t1 = y
L3:
    mayor = $t1
    ifFalse a goto L5
    $t1 = 1
    goto L6
L5:
    $t1 = 2
L6:
    t2 = $t1
    ifFalse a goto L8
    ifFalse b goto L8
    $t1 = "si"
    goto L9
L8:
    $t1 = "no"
L9:
    t3 = $t1
    if x >= y goto L12
    ifFalse a goto L15
    $t2 = 10
    goto L16
L15:
    $t2 = 20
L16:
    $t1 = $t2
    goto L13
L12:
    $t1 = 30
L13:
    t4 = $t1
    ifFalse a goto L18
    $t1 = 1.0
    goto L19
L18:
    $t1 = 2.5
L19:
    t5 = $t1
    $t1 = x + 1
    ifFalse a goto L21
    $t2 = 2
    goto L22
L21:
    $t2 = 3
L22:
    $t1 = $t1 * $t2
    t6 = $t1
    ifFalse a goto L24
    $t1 = "uno"
    goto L25
L24:
    $t1 = "dos"
L25:
    print $t1
endfunc
