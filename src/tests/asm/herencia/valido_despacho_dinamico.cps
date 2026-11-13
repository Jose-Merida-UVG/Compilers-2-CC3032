class Animal {
    function hablar(): string { return "..."; }
    function presentar(): string { return this.hablar(); }
}
class Perro : Animal {
    function hablar(): string { return "guau"; }
}
function decir(a: Animal): string { return a.hablar(); }
let p: Animal = new Perro();
print(decir(p));
print(p.presentar());
