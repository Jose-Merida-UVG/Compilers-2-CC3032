class Base {
    var x: integer = 5;
}
class Hija : Base {
    var y: integer = 6;
    function suma(): integer { return this.x + this.y; }
}
let h = new Hija();
print(h.suma());
