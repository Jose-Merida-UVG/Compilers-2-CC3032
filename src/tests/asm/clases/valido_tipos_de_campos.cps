class Ficha {
    var peso: float = 1.5;
    var activa: boolean = true;
    var nombre: string = "ana";
    function constructor(p: float, n: string) { this.peso = p; this.nombre = n; }
    function doble(): float { return this.peso * 2.0; }
}
let f = new Ficha(2.25, "luis");
print(f.peso);
print(f.activa);
print(f.nombre);
print(f.doble());
f.activa = false;
print(f.activa);
f.peso = 3;
print(f.peso);
