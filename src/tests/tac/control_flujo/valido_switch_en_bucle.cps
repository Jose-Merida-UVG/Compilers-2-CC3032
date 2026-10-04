let i: integer = 0;
while (i < 6) {
    switch (i % 3) {
        case 0:
            i = i + 1;
            continue;
        case 1:
            if (i > 3) {
                break;
            }
        default:
            print(i);
    }
    i = i + 1;
}
