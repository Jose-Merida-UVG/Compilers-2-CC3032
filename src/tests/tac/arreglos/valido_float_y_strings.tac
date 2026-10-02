func __main():
    $t1 = newarray 2
    $t1[0] = 1.5
    $t1[1] = 2.5
    notas = $t1
    n = 2
    $t1 = itof n
    notas[0] = $t1
    notas[1] = 3.0
    $t1 = newarray 2
    $t1[0] = "ana"
    $t1[1] = "luis"
    nombres = $t1
    $t1 = nombres[1]
    $t1 = $t1 + "!"
    nombres[0] = $t1
    $t1 = notas[0]
    $t2 = notas[1]
    $t1 = $t1 + $t2
    total = $t1
    $t1 = nombres[0]
    print $t1
endfunc
