function externa(a: integer): integer {
    let total: integer = 100;
    function medio(b: integer): integer {
        function interna(c: integer): integer {
            total = total + a + b + c;
            return total;
        }
        return interna(1) + interna(2);
    }
    let r: integer = medio(10);
    return r + total;
}
print(externa(5));
