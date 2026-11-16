function seguro(a: integer[], i: integer): integer {
    try {
        return a[i];
    } catch (e) {
        return 0;
    }
}
print(seguro([1, 2, 3], 1));
