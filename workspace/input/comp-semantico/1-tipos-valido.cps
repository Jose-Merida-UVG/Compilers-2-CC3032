// Sistema de tipos — todo correcto, cero errores.
let entero: integer = 42;
let flotante: float = 3.14;
let promovido: float = 7;            // integer -> float
let texto: string = "hola" + " mundo";
let bandera: boolean = true;
const PI: float = 3.1416;
let inferido = 100;                  // tipo inferido del inicializador
let aritmetica: integer = 2 + 3 * 4 - 10 % 3;
let mixta: float = 2 + 3.5;          // promoción en aritmética mixta
let logica: boolean = (entero > 0) && !(flotante < 1.0) || false;
let comparacion: boolean = entero == 42;
let ternario: float = bandera ? 1 : 2.5;   // ramas compatibles -> float
let negativo: integer = -entero;
