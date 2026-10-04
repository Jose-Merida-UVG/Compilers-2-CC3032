class Animal {
    var nombre: string = "sin nombre";
    function describir(): string { return "animal: " + this.nombre; }
}
class Gato : Animal {
    function maullar(): string { return "miau"; }
}
let g = new Gato();
print(g.describir());
print(g.maullar());
