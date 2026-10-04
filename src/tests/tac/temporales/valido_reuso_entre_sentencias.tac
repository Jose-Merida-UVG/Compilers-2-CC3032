func __main():
    x = 3
    $t1 = x * 2
    $t1 = $t1 + 1
    y = $t1
    $t1 = y * y
    $t1 = $t1 - x
    z = $t1
    $t1 = x + y
    $t2 = y + z
    $t1 = $t1 * $t2
    w = $t1
    $t1 = z * 2
    $t1 = w - $t1
    x = $t1
    $t1 = x + y
    $t1 = $t1 + z
    $t1 = $t1 + w
    print $t1
    $t1 = x * y
    print $t1
endfunc
