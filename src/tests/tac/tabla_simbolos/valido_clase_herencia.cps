class Animal {
    var nombre: string = "animal";
    var patas: integer = 4;
    function hablar(): string { return "..."; }
}
class Perro : Animal {
    var vivo: boolean = true;
    var raza: string = "criollo";
    function hablar(): string { return "guau"; }
}
let p = new Perro();
print(p.hablar());
