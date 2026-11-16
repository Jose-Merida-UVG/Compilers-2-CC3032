class Animal {
    function hablar(): integer { return 1; }
    function id(): integer { return 10; }
}
class Perro : Animal {
    function hablar(): integer { return 2; }
}
class Gato : Animal {
    function hablar(): integer { return 3; }
}
let zoo: Animal[] = [new Animal(), new Perro(), new Gato()];
let i: integer = 0;
while (i < 3) {
    print(zoo[i].hablar());
    print(zoo[i].id());
    i = i + 1;
}
