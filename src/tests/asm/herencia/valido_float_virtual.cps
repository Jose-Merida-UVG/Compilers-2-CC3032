class Figura {
    function area(): float { return 0.0; }
    function escala(k: float): float { return this.area() * k; }
}
class Cuadrado : Figura {
    var l: float = 2.0;
    function area(): float { return this.l * this.l; }
}
let f: Figura = new Cuadrado();
print(f.area());
print(f.escala(1.5));
