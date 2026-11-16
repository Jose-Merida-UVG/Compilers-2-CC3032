class Punto {
    var x: integer = 0;
    var y: integer = 0;
    function constructor(a: integer, b: integer) { this.x = a; this.y = b; }
}
let p = new Punto(3, 4);
print(p.x);
p.y = p.x + 1;
print(p.y);
