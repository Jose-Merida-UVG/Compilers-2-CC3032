func __main():
    a = true
    b = false
    c = true
    x = 5
    y = 9
    ifFalse a goto L2
    ifFalse b goto L2
    $t1 = true
    goto L3
L2:
    $t1 = false
L3:
    r1 = $t1
    if a goto L5
    ifFalse b goto L6
L5:
    $t1 = true
    goto L7
L6:
    $t1 = false
L7:
    r2 = $t1
    ifFalse a goto L12
    if b goto L9
L12:
    ifFalse c goto L10
L9:
    $t1 = true
    goto L11
L10:
    $t1 = false
L11:
    r3 = $t1
    if a goto L14
    ifFalse b goto L15
    ifFalse c goto L15
L14:
    $t1 = true
    goto L16
L15:
    $t1 = false
L16:
    r4 = $t1
    if a goto L22
    ifFalse b goto L20
L22:
    ifFalse c goto L20
    $t1 = true
    goto L21
L20:
    $t1 = false
L21:
    r5 = $t1
    if x >= y goto L25
    if y >= 10 goto L25
    $t1 = true
    goto L26
L25:
    $t1 = false
L26:
    r6 = $t1
    if x > y goto L28
    if x != 5 goto L29
L28:
    $t1 = true
    goto L30
L29:
    $t1 = false
L30:
    r7 = $t1
    ifFalse a goto L33
    ifFalse b goto L33
    ifFalse c goto L33
    $t1 = true
    goto L34
L33:
    $t1 = false
L34:
    r8 = $t1
    if a goto L37
    if b goto L37
    ifFalse c goto L38
L37:
    $t1 = true
    goto L39
L38:
    $t1 = false
L39:
    r9 = $t1
    if x >= y goto L43
    if a goto L46
    ifFalse b goto L43
L46:
    if c goto L43
    $t1 = true
    goto L44
L43:
    $t1 = false
L44:
    r10 = $t1
    ifFalse r1 goto L49
    ifFalse r2 goto L49
    $t1 = true
    goto L50
L49:
    $t1 = false
L50:
    print $t1
endfunc
