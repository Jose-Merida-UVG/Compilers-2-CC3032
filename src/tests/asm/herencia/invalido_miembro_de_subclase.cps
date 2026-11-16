class Animal { }
class Perro : Animal { function ladrar(): string { return "guau"; } }
let a: Animal = new Animal();
print(a.ladrar());
