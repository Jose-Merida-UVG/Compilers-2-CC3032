// Declarar dos veces la misma variable en el mismo ámbito debe
// reportar error (a diferencia del shadowing en un bloque anidado,
// que sí es válido).
let x: integer = 1;
let x: integer = 2;
