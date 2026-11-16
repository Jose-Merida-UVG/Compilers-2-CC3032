class A { var v: integer = 1; function quien(): string { return "A"; } function dime(): string { return "soy " + this.quien(); } function val(): integer { return this.v; } }
class B : A { var w: integer = 2; function quien(): string { return "B"; } }
class C : B { function quien(): string { return "C"; } function val(): integer { return this.v + this.w * 10; } }
let xs: A[] = [new A(), new B(), new C()];
foreach (x in xs) { print(x.dime()); print(x.val()); }
let b: B = new C(); print(b.quien()); print(b.w);
