// ============================================================
//  Contraparte válida de todo-invalido.cps: ejercita las mismas
//  reglas, todas en su forma correcta. Debe analizar con CERO
//  errores semánticos.
// ============================================================

// ---------- Declaraciones y tipos ---------------------------
let entero: integer = 42;
let flotante: float = 3.14;
let promovido: float = 7;            // integer -> float (promoción)
let texto: string = "hola" + " mundo";
let bandera: boolean = true;
const PI: float = 3.1416;

let inferido = 100;                  // tipo inferido del inicializador
var sinTipo;                         // unknown...
sinTipo = "ahora string";            // ...fijado en la primera asignación

var opcional: string[] = null;       // null en un tipo referencia

// ---------- Operadores --------------------------------------
let suma: integer = 2 + 3 * 4 - 1;
let mixto: float = 2 + 3.5;          // promoción en aritmética mixta
let modulo: integer = 10 % 3;
let logico: boolean = (entero > 0) && !(flotante < 1.0) || false;
let comparado: boolean = entero == 42;
let distinto: boolean = texto != "otro";
let ternario: float = bandera ? 1 : 2.5;   // ramas compatibles -> float
let negativo: integer = -entero;

// ---------- Ámbito y closures -------------------------------
let externa: integer = 1;
{
  let externa: string = "sombreada";  // shadowing legal en bloque anidado
  let interna: integer = 2;
  print(externa);
  print(interna);
}
print(externa);

function contador(inicio: integer): integer {
  let acumulado: integer = inicio;
  function paso(): integer {          // función anidada (closure)
    return acumulado + 1;             // captura del entorno
  }
  return paso();
}

function factorial(n: integer): integer {
  if (n <= 1) { return 1; }           // recursión
  return n * factorial(n - 1);
}

function saludar(nombre: string): string { return "Hola " + nombre; }
function sinRetorno() { print("efecto secundario"); }   // sin anotación = void
function sinAnotar(x) { print(x); }   // parámetro sin anotación: acepta todo

let f1: integer = contador(5);
let f2: integer = factorial(5);
let f3: string = saludar("Compiscript");
sinRetorno();
sinAnotar(1);
sinAnotar("cualquier cosa");

// ---------- Control de flujo --------------------------------
if (entero > 10) { print("mayor"); } else { print("menor"); }

let i: integer = 0;
while (i < 3) {
  i = i + 1;
  if (i == 1) { continue; }
  if (i == 3) { break; }
}

do { i = i - 1; } while (i > 0);

for (let j: integer = 0; j < 3; j = j + 1) {
  print(j);
}

switch (entero) {
  case 42:
    print("la respuesta");
  case 0:
    print("cero");
  default:
    print("otro");
}

try { print("intenta"); } catch (err) { print("falló"); }

// ---------- Arreglos ----------------------------------------
let numeros: integer[] = [1, 2, 3];
let decimales: float[] = [1.5, 2];        // integer se promueve a float
let vacio: integer[] = [];                // arreglo vacío en cualquier arreglo
let matriz: integer[][] = [[1, 2], [3]];
let matrizVacia: integer[][] = [[]];      // vacío anidado
let primero: integer = numeros[0];
let celda: integer = matriz[1][0];
let cadenas: string[] = ["a", "b"];

foreach (n in numeros) {
  print(n + 1);                            // n es integer
}

function sumarTodos(valores: integer[]): integer {
  let total: integer = 0;
  foreach (v in valores) {
    total = total + v;
  }
  return total;
}
let totalizado: integer = sumarTodos(numeros);

// ---------- Clases y objetos --------------------------------
class Animal {
  var nombre: string;
  var edad: integer;
  const PATAS: integer = 4;

  function constructor(nombre: string, edad: integer) {
    this.nombre = nombre;
    this.edad = edad;
  }

  function describir(): string {
    return this.nombre;
  }
}

class Perro : Animal {
  var raza: string;

  function ladrar(): string {
    return this.nombre + " dice guau";
  }
}

let animal: Animal = new Animal("Genérico", 3);
let perro: Perro = new Perro("Fido", 2);   // constructor heredado

let leido: string = perro.nombre;          // atributo heredado
let patas: integer = perro.PATAS;          // constante heredada
let ladrido: string = perro.ladrar();      // método propio
let desc: string = perro.describir();      // método heredado

perro.raza = "labrador";                   // escritura de atributo propio
print(perro.raza = "collie");              // asignación de propiedad anidada
                                           // en una expresión (via visitAssignExpr)
perro.edad = perro.edad + 1;               // lectura + escritura heredada

let comoBase: Animal = perro;              // subclase asignable a la base
let objetos: Animal[] = [animal];
let nulo: Animal = null;                   // null en tipo clase

print(ladrido);
print(desc);
print(totalizado);
