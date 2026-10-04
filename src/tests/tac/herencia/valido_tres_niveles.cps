class A {
    var a: integer = 1;
    function quien(): string { return "A"; }
    function soloA(): integer { return this.a; }
}
class B : A {
    var b: integer = 2;
    function quien(): string { return "B"; }
}
class C : B {
    var c: integer = 3;
    function suma(): integer { return this.a + this.b + this.c; }
}
let x = new C();
print(x.quien());
print(x.soloA());
print(x.suma());
