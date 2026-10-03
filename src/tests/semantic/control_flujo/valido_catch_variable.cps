let a = [1, 2, 3];
try {
    let x = a[10];
} catch (err) {
    print("Error atrapado: " + err);
}
try { print("a"); } catch (err) { print(err); }
