class Animal {
  var nombre: string;

  function constructor(nombre: string) {
    this.nombre = nombre;
  }

  function saludar(): string {
    return this.nombre;
  }
}

let a = new Animal("Rex");
let saludo: string = a.saludar();
