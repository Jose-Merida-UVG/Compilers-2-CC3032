class Animal {
    var nombre: string;
    function constructor(n: string) { this.nombre = n; }
}
class Perro : Animal {
    var raza: string = "criollo";
    function info(): string { return this.nombre + " (" + this.raza + ")"; }
}
let p = new Perro("rex");
p.nombre = "max";
print(p.info());
