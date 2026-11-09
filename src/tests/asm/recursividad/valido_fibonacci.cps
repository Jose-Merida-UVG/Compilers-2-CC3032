function fib(n: integer): integer {
    if (n < 2) {
        return n;
    }
    return fib(n - 1) + fib(n - 2);
}
for (let i: integer = 0; i < 8; i = i + 1) {
    print(fib(i));
}
print(fib(10));
