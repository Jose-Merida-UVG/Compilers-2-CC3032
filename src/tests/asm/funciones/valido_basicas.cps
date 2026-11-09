function suma(a: integer, b: integer): integer {
    return a + b;
}
function saluda(nombre: string) {
    print("hola " + nombre);
}
function sinParametros(): integer {
    return 42;
}
print(suma(2, 3));
saluda("mundo");
print(sinParametros());
let r: integer = suma(10, suma(1, 2));
print(r);
