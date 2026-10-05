// Demo — herencia: método sobrescrito, método heredado, campo heredado,
// constructor heredado y cadena de tres niveles.
class Animal {
    var nombre: string;
    function constructor(n: string) { this.nombre = n; }
    function hablar(): string { return "..."; }
    function describir(): string { return "animal: " + this.nombre; }
}
class Perro : Animal {
    var raza: string = "criollo";
    function hablar(): string { return "guau"; }
}
class A { var a: integer = 1; function quien(): string { return "A"; } }
class B : A { var b: integer = 2; function quien(): string { return "B"; } }
class C : B { var c: integer = 3; function suma(): integer { return this.a + this.b + this.c; } }

let p = new Perro("rex");
print(p.hablar());      // Perro.hablar (sobrescrito)
print(p.describir());   // Animal.describir (heredado)
p.nombre = "max";       // campo heredado
let x = new C();
print(x.quien());       // B.quien (ancestro más cercano)
print(x.suma());
