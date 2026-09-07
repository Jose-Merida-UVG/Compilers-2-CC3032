// Funciones — todo correcto, cero errores.
function saludar(nombre: string): string { return "Hola " + nombre; }
function sinRetorno() { print("sin anotación = void"); }
function sinAnotar(x) { print(x); }          // parámetro sin anotación: acepta todo

function factorial(n: integer): integer {    // recursión
  if (n <= 1) { return 1; }
  return n * factorial(n - 1);
}

function contador(inicio: integer): integer {
  let acumulado: integer = inicio;
  function paso(): integer {                 // función anidada (closure)
    return acumulado + 1;                    // captura del entorno
  }
  return paso();
}

function ambasRamas(n: integer): integer {   // retorno garantizado por if/else
  if (n > 0) { return 1; } else { return 2; }
}

// --- multi-parámetro ---
function sumar(a: integer, b: integer): integer { return a + b; }

function describir(nombre: string, edad: integer, activo: boolean): string {
  // varios tipos distintos de parámetro
  if (edad > 0 && activo) { return nombre + " está activo"; }
  return nombre + " está inactivo";
}

function promedio(x: float, y: float, z: float): float {
  return (x + y + z) / 3.0;
}

function mixtos(a, b: integer, c) {          // algunos parámetros sin anotar (aceptan todo)
  print(a);
  print(b + 1);
  print(c);
}

function sumarTres(a: integer, b: integer, c: integer): integer {
  return sumar(a, b) + c;                    // llama a otra función multi-parámetro
}

print(saludar("Compiscript"));
print(factorial(5));
print(contador(5));
print(ambasRamas(1));
sinRetorno();
sinAnotar(1);
sinAnotar("cualquier cosa");

print(sumar(2, 3));
print(describir("Ana", 30, true));
print(promedio(1.0, 2.0, 3.0));
mixtos("uno", 2, true);
print(sumarTres(1, 2, 3));
