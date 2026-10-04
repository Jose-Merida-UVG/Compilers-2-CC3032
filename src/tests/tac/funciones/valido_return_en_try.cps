function primero(a: integer[]): integer {
    try { return a[0]; } catch (e) { print(e); }
    return 0;
}
let xs = [7, 8];
print(primero(xs));
