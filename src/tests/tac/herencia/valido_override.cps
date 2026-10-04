class Animal {
    function hablar(): string { return "..."; }
}
class Perro : Animal {
    function hablar(): string { return "guau"; }
}
let a = new Animal();
let p = new Perro();
print(a.hablar());
print(p.hablar());
