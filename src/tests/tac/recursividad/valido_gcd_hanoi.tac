func gcd(a, b):
    if b != 0 goto L2
    return a
L2:
    $t1 = a % b
    param b
    param $t1
    $t1 = call gcd, 2
    return $t1
endfunc
func hanoi(n, origen, destino, auxiliar):
    if n != 0 goto L4
    return
L4:
    $t1 = n - 1
    param $t1
    param origen
    param auxiliar
    param destino
    call hanoi, 4
    $t1 = origen + " -> "
    $t1 = $t1 + destino
    print $t1
    $t1 = n - 1
    param $t1
    param auxiliar
    param destino
    param origen
    call hanoi, 4
    return
endfunc
func __main():
    param 48
    param 18
    $t1 = call gcd, 2
    print $t1
    param 2
    param "A"
    param "C"
    param "B"
    call hanoi, 4
endfunc
