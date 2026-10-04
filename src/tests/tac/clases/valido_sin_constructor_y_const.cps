class Config {
    const VERSION: string = "1.0";
    var activo: boolean = true;
    var factor: float = 2;
}
let c = new Config();
print(c.VERSION);
print(c.activo);
print(c.factor);
