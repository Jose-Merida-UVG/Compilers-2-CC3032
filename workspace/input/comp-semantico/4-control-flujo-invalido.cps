// Control de flujo — un error por línea marcada con [n].
if (1) { }                           // [1] condición de if
while ("x") { }                      // [2] condición de while
do { } while (5);                    // [3] condición de do-while
for (let i: integer = 0; 7; ) { }    // [4] condición de for
switch (1) { case "s": print(1); }   // [5] case incompatible con switch
break;                               // [6] break fuera de bucle
continue;                            // [7] continue fuera de bucle
return 1;                            // [8] return fuera de función
