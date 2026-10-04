func saludar():
    print "hola"
    return
endfunc
func cuadrado(x):
    $t1 = x * x
    return $t1
endfunc
func suma(a, b):
    $t1 = a + b
    return $t1
endfunc
func promedio(a, b):
    $t1 = a + b
    $t1 = $t1 / 2.0
    return $t1
endfunc
func esPar(n):
    $t1 = n % 2
    $t1 = $t1 == 0
    return $t1
endfunc
func __main():
    call saludar, 0
    param 4
    $t1 = call cuadrado, 1
    print $t1
    param 2
    param 3
    $t1 = call suma, 2
    s = $t1
    param 1.0
    param 2.0
    $t1 = call promedio, 2
    print $t1
    param s
    $t1 = call esPar, 1
    print $t1
endfunc
