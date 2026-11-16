function sumaMas(n: integer, m: integer): integer {
    function agrega(x: integer): integer {
        return x + n * m;
    }
    return agrega(1) + agrega(2);
}
print(sumaMas(3, 4));
print(sumaMas(1, 1));
