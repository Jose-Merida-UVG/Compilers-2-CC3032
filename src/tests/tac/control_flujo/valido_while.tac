func __main():
    i = 0
    suma = 0
L1:
    if i >= 10 goto L3
    $t1 = suma + i
    suma = $t1
    $t1 = i + 1
    i = $t1
    goto L1
L3:
    print suma
L4:
    if suma <= 0 goto L6
    $t1 = suma - 7
    suma = $t1
    goto L4
L6:
endfunc
