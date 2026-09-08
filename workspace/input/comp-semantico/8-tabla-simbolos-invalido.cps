// Contraparte de 8-tabla-simbolos-valido.cps: cada error de aquí solo es
// posible porque el checker recuperó o actualizó una entrada real de la
// tabla de símbolos. El mensaje de cada error cita el tipo que se
// recuperó/actualizó -- esa es la evidencia, ya que esta fase no ejecuta
// nada (no hay valores en tiempo de ejecución, solo tipos estáticos).

// --- Recuperar: el error solo puede salir si 'nombre' fue resuelto ---
let nombre: string = "Ana";
let x: integer = nombre; // [1] recupera 'nombre' -> string, no calza con integer

// --- Actualizar: el error solo puede salir si la entrada de 'y' cambió ---
let y;          // entra a la tabla como "unknown"
y = 5;          // primera asignación: la entrada se actualiza a integer
y = "hola";     // [2] ya no es "unknown": ahora se compara contra integer

// --- Actualizar (miembro de clase): mismo mecanismo, otra tabla ---
class Caja {
  var contenido: integer;
  function constructor(inicial: integer) { this.contenido = inicial; }
}
let caja: Caja = new Caja(1);
caja.contenido = "texto"; // [3] recupera el tipo de 'contenido' -> integer, no calza
