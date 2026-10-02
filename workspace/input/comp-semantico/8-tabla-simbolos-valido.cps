// Caso integral: funcionamiento de la tabla de símbolos.
// No hay ejecución en esta fase (sin intérprete/codegen todavía), así
// que lo que demuestra cada punto es el ÁRBOL DE ÁMBITOS que produce el
// análisis semántico (panel "Tabla de símbolos" del IDE), no la salida
// de ningún print. Cada sección deja símbolos distintos en ese árbol
// para poder señalarlos ahí.

// --- 1. Insertar ---
let contador;                     // integer, tras narrowing en la línea 11
let nombre: string = "Ana";
const limite: integer = 10;
class Cuenta {
  var saldo: integer;
  const MONEDA: string = "GTQ";
  function constructor(inicial: integer) { this.saldo = inicial; }
}
function calcular(base: integer, factor: float): float { return base * factor; }

// --- 2. Recuperar ---
// El checker resuelve cada nombre contra la tabla ya construida y usa
// el tipo que recupera para tipar lo que lo usa.
let copia: integer = contador;               // recupera 'contador' -> integer
let usoFuncion: float = calcular(2, 1.5);    // recupera la firma de 'calcular'
let cuenta: Cuenta = new Cuenta(100);        // recupera la clase 'Cuenta' y su constructor
let usoMiembro: integer = cuenta.saldo;      // recupera un miembro de 'Cuenta'

// --- 3. Actualizar ---
// La asignación ocurre en un bloque anidado, pero no hay 'let' ahí: no
// se inserta un símbolo nuevo, se reasigna el mismo 'contador' global
// (resolve() sube hasta encontrarlo). Con eso, su entrada en la tabla
// pasa de "unknown" a "integer" -- la misma entrada, tipo actualizado.
{
  contador = 0;
}
contador = contador + 1;
nombre = nombre + " Pérez";

// --- 4. Manejo de alcances ---
// Cada '{ }', función y clase abre su propio ámbito en el árbol.
{
  // ámbito de bloque: sombrea 'contador' del global; 'local' solo existe aquí
  let contador: integer = 100;
  let local: integer = contador + limite;
}
// aquí 'contador' vuelve a resolver al del ámbito global

function actualizarEnAmbito(x: integer): integer {
  // ámbito de función: 'x' es un símbolo propio de este ámbito
  let y: integer = x * 2;
  {
    let y: integer = y * 2; // ámbito anidado: sombrea la 'y' de la función (no la lee)
  }
  return x;
}
