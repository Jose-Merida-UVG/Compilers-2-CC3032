class Nodo { var val: integer; var sig: Nodo;
  function constructor(v: integer, s: Nodo) { this.val = v; this.sig = s; } }
class Lista { var cab: Nodo = null;
  function push(v: integer) { this.cab = new Nodo(v, this.cab); }
  function suma(): integer { let t: integer = 0; let p: Nodo = this.cab; while (p != null) { t = t + p.val; p = p.sig; } return t; }
  function sumaRec(n: Nodo): integer { if (n == null) { return 0; } return n.val + this.sumaRec(n.sig); } }
let l: Lista = new Lista();
for (let i: integer = 1; i <= 100; i = i + 1) { l.push(i); }
print(l.suma()); print(l.sumaRec(l.cab));
let arr: Lista[] = [new Lista(), new Lista()]; arr[1].push(5); arr[1].push(6); print(arr[1].suma() + arr[0].suma());
let str: string = ""; foreach (n in [1, 2, 3]) { str = str + "n,"; } print(str);
print("x=" + "y");
