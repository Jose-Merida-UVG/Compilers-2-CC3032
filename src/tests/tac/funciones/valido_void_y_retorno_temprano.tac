func mostrar(n):
    if n >= 0 goto L2
    print "negativo"
    return
L2:
    print n
    return
endfunc
func signo(n):
    if n <= 0 goto L4
    return 1
L4:
    if n >= 0 goto L7
    return -1
L7:
    return 0
endfunc
func __main():
    param -1
    call mostrar, 1
    param 5
    call mostrar, 1
    param 3
    $t1 = call signo, 1
    print $t1
endfunc
