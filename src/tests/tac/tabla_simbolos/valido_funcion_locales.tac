func mezcla(a, b, c):
    x = a
    activo = b
    y = c
    $t1 = x + 1
    z = $t1
    x = z
    ifFalse activo goto L2
    return x
L2:
    param x
    param false
    param y
    $t1 = call mezcla, 3
    return $t1
endfunc
func __main():
    param 1
    param true
    param 2.0
    $t1 = call mezcla, 3
    print $t1
endfunc
