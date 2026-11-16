let x: integer = 1;
try {
    if (x > 0) {
        print("positivo");
    } else {
        print("no positivo");
    }
    foreach (v in [1, 2]) {
        print(v);
    }
} catch (e) {
    x = 0;
    print("error: " + e);
}
