// Acceso '.' sobre una variable declarada con anotación de clase, incluida
// herencia: la anotación debe reusar el ClassType real (con miembros), no
// construir uno vacío. Ver _resolve_type_node.
class A {
  var n: integer;
  function met(x: integer): integer { return x; }
}
class B : A {
  var m: string;
}
var b: B = new B();
var leido: integer = b.n;
var heredado: integer = b.met(1);
b.n = 5;
b.m = "ok";
b.n = b.n + 1;
