// Lado de escritura de '.': el miembro debe existir, no ser constante, y el
// valor debe caber en su tipo.
class A {
  var n: integer;
  const K: integer = 1;
}
var a: A = new A();
a.n = "mal";
a.noExiste = 1;
a.K = 9;
