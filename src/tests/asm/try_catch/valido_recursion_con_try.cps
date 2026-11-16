function f(n: integer, a: integer[]): integer {
    try {
        if (n == 0) {
            return a[9];
        }
        return f(n - 1, a) + 1;
    } catch (e) {
        return 100;
    }
}
print(f(3, [1]));
