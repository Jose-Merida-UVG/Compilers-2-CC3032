let i: integer = 0;
while (true) {
    i = i + 1;
    if (i == 3) {
        continue;
    }
    if (i > 6) {
        break;
    }
    print(i);
}
for (let k: integer = 0; k < 10; k = k + 1) {
    if (k % 2 == 0) {
        continue;
    }
    if (k > 7) {
        break;
    }
    print(k);
}
let a: integer = 0;
while (a < 3) {
    let b: integer = 0;
    while (b < 3) {
        if (b == 1) {
            break;
        }
        b = b + 1;
    }
    a = a + 1;
}
