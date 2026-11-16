function primero_par(a: integer[]): integer {
    foreach (x in a) {
        try {
            if (x % 2 == 0) {
                return x;
            }
        } catch (e) {
            print(e);
        }
    }
    return -1;
}
print(primero_par([1, 3, 4, 6]));
