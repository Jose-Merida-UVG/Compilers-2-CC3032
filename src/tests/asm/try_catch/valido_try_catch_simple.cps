let a = [1, 2, 3];
try {
    let peligro = a[100];
    print(peligro);
} catch (err) {
    print("Error atrapado: " + err);
}
print("fin");
