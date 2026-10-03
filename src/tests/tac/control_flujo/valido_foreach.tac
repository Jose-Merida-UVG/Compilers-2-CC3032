func __main():
    $t1 = newarray 3
    $t1[0] = 10
    $t1[1] = 20
    $t1[2] = 30
    notas = $t1
    suma = 0
    $t1 = len notas
    $t2 = 0
L1:
    if $t2 >= $t1 goto L3
    n = notas[$t2]
    $t3 = suma + n
    suma = $t3
    $t2 = $t2 + 1
    goto L1
L3:
    print suma
    $t1 = newarray 2
    $t1[0] = "ana"
    $t1[1] = "luis"
    nombres = $t1
    $t1 = len nombres
    $t2 = 0
L4:
    if $t2 >= $t1 goto L6
    nombre = nombres[$t2]
    $t3 = "hola " + nombre
    print $t3
    $t2 = $t2 + 1
    goto L4
L6:
    $t1 = newarray 2
    $t2 = newarray 2
    $t2[0] = 1
    $t2[1] = 2
    $t1[0] = $t2
    $t2 = newarray 2
    $t2[0] = 3
    $t2[1] = 4
    $t1[1] = $t2
    m = $t1
    $t1 = len m
    $t2 = 0
L7:
    if $t2 >= $t1 goto L9
    fila = m[$t2]
    $t3 = len fila
    $t4 = 0
L10:
    if $t4 >= $t3 goto L12
    v = fila[$t4]
    print v
    $t4 = $t4 + 1
    goto L10
L12:
    $t2 = $t2 + 1
    goto L7
L9:
    $t1 = newarray 3
    $t1[0] = 5
    $t1[1] = 6
    $t1[2] = 7
    $t2 = len $t1
    $t3 = 0
L13:
    if $t3 >= $t2 goto L15
    x = $t1[$t3]
    if x != 6 goto L17
    goto L14
L17:
    if x <= 6 goto L19
    goto L15
L19:
    print x
L14:
    $t3 = $t3 + 1
    goto L13
L15:
endfunc
