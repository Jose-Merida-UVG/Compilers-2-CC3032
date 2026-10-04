func __main():
    $t1 = newarray 3
    $t1[0] = 10
    $t1[1] = 20
    $t1[2] = 30
    notas = $t1
    total = 0
    $t1 = len notas
    $t2 = 0
L1:
    if $t2 >= $t1 goto L3
    n = notas[$t2]
    $t3 = n * 2
    $t3 = total + $t3
    $t4 = n - 1
    $t3 = $t3 + $t4
    total = $t3
    $t2 = $t2 + 1
    goto L1
L3:
    $t1 = total + 1
    if $t1 == 1 goto L4
    goto L5
L4:
    $t1 = total * 2
    $t1 = $t1 + 1
    print $t1
L5:
    $t1 = notas[1]
    $t1 = $t1 * 3
    $t1 = total + $t1
    print $t1
endfunc
