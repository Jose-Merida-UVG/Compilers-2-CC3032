// Mirilla — codigo_muerto: instrucciones entre un `j`/`jr` y la siguiente etiqueta se quitan.
// Un `return` dentro de `try` deja un salto y código detrás que nadie ejecuta.
function seguro(a: integer[], i: integer): integer {
    try {
        return a[i];
    } catch (e) {
        return 0;
    }
}
print(seguro([1, 2, 3], 1));
