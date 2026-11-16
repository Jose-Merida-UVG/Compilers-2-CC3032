// Mirilla — fusion_ajustes_sp: dos `addiu $sp,$sp,N` seguidos se funden en uno
// (o desaparecen si suman 0). Pasa con llamadas consecutivas.
function mostrar(n: integer) { print(n); }
mostrar(1);
mostrar(2);
mostrar(3);
