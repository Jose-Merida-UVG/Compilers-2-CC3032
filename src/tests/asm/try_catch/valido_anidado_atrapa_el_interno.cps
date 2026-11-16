let a = [1];
try {
    print("a");
    try {
        print(a[5]);
    } catch (e1) {
        print("interno");
    }
    print("b");
} catch (e2) {
    print("externo");
}
