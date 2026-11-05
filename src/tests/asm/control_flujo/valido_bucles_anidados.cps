for (let i: integer = 1; i <= 3; i = i + 1) {
    for (let j: integer = 1; j <= 3; j = j + 1) {
        if (j == 2) {
            continue;
        }
        if (i == 3) {
            break;
        }
        print(i * 10 + j);
    }
}
