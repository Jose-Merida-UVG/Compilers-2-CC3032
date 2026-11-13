class Caja {
    var v: integer = 0;
    function constructor(x: integer) { this.v = x; }
}
function llena(c: Caja) { c.v = 99; }
let cajas: Caja[] = [new Caja(1), new Caja(2)];
llena(cajas[1]);
print(cajas[0].v);
print(cajas[1].v);
