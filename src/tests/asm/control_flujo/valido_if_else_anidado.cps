function clasifica(n: integer) {
    if (n < 0) {
        print("negativo");
    } else {
        if (n == 0) {
            print("cero");
        } else {
            if (n < 10) {
                print("pequeno");
            } else {
                print("grande");
            }
        }
    }
}
clasifica(-5);
clasifica(0);
clasifica(7);
clasifica(42);
