// Demo — clases con errores: no se genera TAC.
class P { var x: integer = 0; function constructor(a: integer) { this.x = a; } }
let p = new P(1, 2);     // argumentos del constructor
print(p.z);              // miembro inexistente
p.x = "texto";           // tipo de campo
print(this);             // this fuera de una clase
