try {
    print("externo");
    try {
        print("interno");
    } catch (e1) {
        print(e1);
    }
} catch (e2) {
    print("fallo " + e2);
}
