function externa(n: integer): integer {
    function interna(m: integer): integer { return m + 1; }
    let r = interna(n);
    return r * 2;
}
print(externa(3));
