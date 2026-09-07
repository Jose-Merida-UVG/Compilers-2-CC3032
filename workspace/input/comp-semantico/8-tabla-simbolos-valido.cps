// Caso integral: funcionamiento de la tabla de símbolos
// Cubre: insertar, recuperar, actualizar y manejo de alcances.

// --- 1. Insertar (declare en el ámbito global) ---
let contador: integer = 0;
let nombre: string = "Ana";
const limite: integer = 10;

// --- 2. Recuperar información (resolve: leer un símbolo ya insertado) ---
print(contador);
print(nombre);
print(limite);
let copia: integer = contador; // recupera el tipo/valor de "contador" para tipar "copia"

// --- 3. Actualizar información (reasignar; el símbolo mantiene su entrada, cambia su valor) ---
contador = contador + 1;
nombre = nombre + " Pérez";
print(contador);
print(nombre);

// --- 4. Manejo de alcances (enter_scope / exit_scope, shadowing y resolución por ámbito) ---
{
  // nuevo ámbito de bloque: "contador" sombrea al global, "local" solo existe aquí
  let contador: integer = 100;
  let local: integer = contador + limite; // resuelve "contador" local y "limite" global (padre)
  print(contador);
  print(local);
}
print(contador); // al salir del bloque, vuelve a resolverse el "contador" global (ya actualizado a 1)

function actualizarEnAmbito(x: integer): integer {
  // ámbito de función: "x" (parámetro) se inserta aquí y se recupera/actualiza dentro
  x = x * 2;          // actualizar dentro del ámbito de función
  let y: integer = x;  // insertar y recuperar dentro del mismo ámbito
  let z: integer = y + limite; // recupera "y" del ámbito de función y "limite" del global
  {
    let y: integer = z; // ámbito anidado: sombrea "y" de la función (no lo modifica)
    print(y);
  }
  print(y); // fuera del bloque interno, "y" vuelve a ser el de la función (sin modificar)
  return x;
}

print(actualizarEnAmbito(5));
print(contador); // confirma que el ámbito de la función no afectó al "contador" global
