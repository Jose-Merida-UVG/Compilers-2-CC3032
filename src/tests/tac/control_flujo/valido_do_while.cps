let i: integer = 0;
do {
    print(i);
    i = i + 1;
} while (i < 3);
let n: integer = 10;
do {
    n = n - 1;
    if (n == 5) {
        continue;
    }
    print(n);
} while (n > 0);
