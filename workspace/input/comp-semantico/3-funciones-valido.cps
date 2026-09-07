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

print(saludar("Compiscript"));
print(factorial(5));
print(contador(5));
print(ambasRamas(1));
sinRetorno();
sinAnotar(1);
sinAnotar("cualquier cosa");
