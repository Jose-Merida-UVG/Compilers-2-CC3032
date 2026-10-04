func __main():
    x = 1
    if x == 1 goto L1
    if x == 2 goto L2
    goto L3
L1:
    print "uno"
L2:
    print "dos"
L3:
    print "otro"
    dia = 3
    if dia == 1 goto L5
    if dia == 2 goto L6
    goto L7
L5:
    print "lunes"
L6:
    print "martes"
L7:
    nombre = "b"
    if nombre == "a" goto L8
    if nombre == "b" goto L9
    goto L10
L8:
    print "A"
L9:
    print "B"
L10:
    suma = 0
    $t1 = suma + 1
    if $t1 == 0 goto L11
    goto L12
L11:
    suma = 10
L12:
    $t1 = suma + 1
    suma = $t1
endfunc
