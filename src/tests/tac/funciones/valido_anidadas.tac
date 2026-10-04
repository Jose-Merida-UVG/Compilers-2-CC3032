func externa(n):
    param n
    $t1 = call interna, 1
    r = $t1
    $t1 = r * 2
    return $t1
endfunc
func interna(m):
    $t1 = m + 1
    return $t1
endfunc
func __main():
    param 3
    $t1 = call externa, 1
    print $t1
endfunc
