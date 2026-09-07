// ============================================================
//  DEMO — Tabla de símbolos
//  Cada sección corresponde a un punto de la rúbrica.
//  Correr con ▶ y mirar la pestaña "symbols".
// ============================================================

// ---- (1) INSERTAR: un símbolo de cada kind ------------------
var variable: integer = 1;           // VARIABLE
const CONSTANTE: float = 3.14;       // CONSTANT
class Cuenta {                       // CLASS
  var saldo: integer;                // VARIABLE (miembro)
  const MONEDA: string = "GTQ";      // CONSTANT (miembro)
  function constructor(inicial: integer) {   // FUNCTION + PARAMETER
    this.saldo = inicial;
  }
  function depositar(monto: integer): integer {
    this.saldo = this.saldo + monto;
    return this.saldo;
  }
}
function calcular(base: integer, factor: float): float {  // FUNCTION + 2 PARAMETER
  return base * factor;
}

// ---- (2) RECUPERAR: se usa lo insertado ---------------------
// El checker resuelve cada nombre en la tabla y usa el tipo que
// recupera. Si el tipo recuperado no calza, reporta error.
let usoVariable: integer = variable;         // recupera 'variable' -> integer
let usoConstante: float = CONSTANTE;         // recupera 'CONSTANTE' -> float
let usoFuncion: float = calcular(2, 1.5);    // recupera la firma y valida args
let cuenta: Cuenta = new Cuenta(100);        // recupera la clase y su constructor
let usoMiembro: integer = cuenta.depositar(50);   // recupera un miembro
let usoHeredado: string = cuenta.MONEDA;     // recupera una constante miembro

// ---- (3) ACTUALIZAR: el tipo del símbolo cambia -------------
// 'porResolver' se inserta con tipo 'unknown' porque no tiene
// anotación ni valor inicial. La primera asignación ACTUALIZA
// el símbolo ya insertado, en el mismo lugar de la tabla.
//
//   DEMO EN VIVO: correr así -> el panel muestra 'unknown'.
//   Descomentar la línea de abajo, volver a correr
//   -> el mismo símbolo ahora muestra 'integer'.
var porResolver;
// porResolver = 7;

// ---- (4) ALCANCES: un entorno por construcción --------------
let visible: string = "global";
{                                    // BLOCK anidado
  let visible: string = "sombra";    // mismo nombre, otro ámbito: legal
  let soloAqui: integer = 99;        // vive solo en este bloque
  print(visible);
  print(soloAqui);
}
print(visible);                      // vuelve a ser el global

function conAmbitos(p: integer): integer {   // FUNCTION scope: p
  let local: integer = p * 2;                // BLOCK scope del cuerpo
  {
    let masAdentro: integer = local + 1;     // BLOCK anidado
    print(masAdentro);
  }
  return local;
}
print(conAmbitos(4));
