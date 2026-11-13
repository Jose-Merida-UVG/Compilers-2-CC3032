// Demo — funciones y parámetros (TAC): llamadas, void, retorno temprano,
// funciones anidadas y llamadas como argumento.
function saludar() { print("hola"); }
function suma(a: integer, b: integer): integer { return a + b; }
function promedio(a: float, b: float): float { return (a + b) / 2.0; }
function doble(x: integer): integer { return x * 2; }
function mostrar(n: integer) {
    if (n < 0) { print("negativo"); return; }
    print(n);
}
function externa(n: integer): integer {
    function interna(m: integer): integer { return m + 1; }
    return interna(n) * 2;
}

saludar();
print(suma(2, 3));
print(promedio(1, 2));
print(suma(doble(2), doble(3)));
mostrar(-1);
mostrar(5);
print(externa(3));
