let i: integer = 0;
while (i < 5) {
    i = i + 1;
    try {
        if (i == 2) {
            continue;
        }
        if (i == 4) {
            break;
        }
        print(i);
    } catch (e) {
        print(e);
    }
}
for (let k: integer = 0; k < 3; k = k + 1) {
    try {
        print(k);
    } catch (err) {
        print("x");
    }
}
