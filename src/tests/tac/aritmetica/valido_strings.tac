func __main():
    nombre = "mundo"
    $t1 = "Hola " + nombre
    saludo = $t1
    $t1 = "a" + "b"
    $t1 = $t1 + "c"
    $t1 = $t1 + nombre
    largo = $t1
    print saludo
    $t1 = "Hola " + nombre
    $t1 = $t1 + "!"
    print $t1
endfunc
