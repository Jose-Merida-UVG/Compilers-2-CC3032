// Declarar dos clases con el mismo nombre en el mismo ámbito debe
// reportar error.
class Foo {
  var a: integer;
}

class Foo {
  var b: string;
}
