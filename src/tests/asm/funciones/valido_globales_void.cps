let contador: integer = 0;
function incrementa() {
    contador = contador + 1;
}
function mostrar() {
    print(contador);
}
incrementa();
incrementa();
mostrar();
function temprano(n: integer) {
    if (n > 3) {
        return;
    }
    print(n);
}
temprano(1);
temprano(5);
temprano(3);
