class Calc {
    function fact(n: integer): integer {
        if (n <= 1) { return 1; }
        return n * this.fact(n - 1);
    }
    function pot(b: integer, e: integer): integer {
        if (e == 0) { return 1; }
        return b * pot(b, e - 1);
    }
}
let c = new Calc();
print(c.fact(5));
print(c.pot(2, 3));
