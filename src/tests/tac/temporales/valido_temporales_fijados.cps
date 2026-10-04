let notas = [10, 20, 30];
let total: integer = 0;
foreach (n in notas) {
    total = total + n * 2 + (n - 1);
}
switch (total + 1) {
    case 1:
        print(total * 2 + 1);
    default:
        print(total + notas[1] * 3);
}
