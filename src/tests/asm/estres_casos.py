"""Casos de estrés del generador de MIPS: (área, nombre, programa, salida esperada).

La salida esperada es el texto exacto o `("has", texto)` si solo importa que aparezca.
Los corre `test_asm_estres.py`.
"""
def L(*xs): return "".join(str(x) + "\n" for x in xs)
C = []
def add(area, name, src, exp): C.append((area, name, src, exp))

# ---------------- declaraciones
add("declaraciones","tipos_basicos",'''
let a: integer = 7; const K: integer = 3; let s: string = "hi"; let f: float = 2.5; let b: boolean = true; let n = 10;
print(a); print(K); print(s); print(f); print(b); print(n);''', L(7,3,"hi",2.5,"true",10))
add("declaraciones","sombra_en_bloques",'''
let x: integer = 1;
{ let x: integer = 2; print(x); { let x: integer = 3; print(x); } print(x); }
print(x);''', L(2,3,2,1))
add("declaraciones","sin_inicializar_luego_asignar",'''
let x: integer; x = 5; print(x);''', L(5))
add("declaraciones","globales_mezclados_bool_1byte",'''
let a: boolean = true; let b: integer = 9; let c: boolean = false; let d: float = 1.5; let e: string = "z"; let f: boolean = true;
print(a); print(b); print(c); print(d); print(e); print(f);''', L("true",9,"false",1.5,"z","true"))
add("declaraciones","locales_en_funcion_con_bloques",'''
function f(): integer {
  let a: integer = 1;
  { let b: integer = 2; { let c: integer = 3; a = a + b + c; } }
  let d: integer = 10;
  return a + d;
}
print(f());''', L(16))

# ---------------- aritmetica
add("aritmetica","division_y_modulo_con_signo",'''
let x: integer = 7; let y: integer = 2; let n: integer = -7; let t: integer = 3;
print(x / y); print(n / y); print(x % t); print(n % t); print(x - t - y); print(2 + x * t);''', L(3,-3,1,-1,2,23))
add("aritmetica","floats_y_mezcla",'''
let i: integer = 3; let f: float = 0.5;
print(i + f); print(i * f); print(f / 2); print(i / 2); print(10.0 / 4.0); print(-f);''', L(3.5,1.5,0.25,1,2.5,-0.5))
add("aritmetica","expresion_con_muchos_vivos",'''
let a: integer = 1; let b: integer = 2; let c: integer = 3; let d: integer = 4;
let e: integer = 5; let f: integer = 6; let g: integer = 7; let h: integer = 8;
print((a + b) * (c + d) + (e + f) * (g + h));''', L(186))
add("aritmetica","desbordamiento_da_la_vuelta",'''
let m: integer = 2147483647; print(m + 1);''', L(-2147483648))
add("aritmetica","inmediatos_y_potencias_de_2",'''
let x: integer = 5; print(x * 8); print(x * 3); print(x + 32767); print(x - 32768); print(x + 100000); print(x * 1024);''', L(40,15,32772,-32763,100005,5120))
add("aritmetica","unario",'''
let x: integer = 5; let y: integer = -x; print(y); print(-(-x)); print(-x * 2); print(- 3 + x);''', L(-5,5,-10,2))
add("aritmetica","division_por_cero_observar",'''
let z: integer = 0; print(10 / z); print("sigue");''', ("has","sigue"))

# ---------------- logicas
add("logicas","operadores_basicos",'''
print(true && false); print(true || false); print(!true); print(3 < 4); print(3 >= 4); print(3 == 3); print(3 != 3);
print("a" == "a"); print("a" != "b");''', L("false","true","false","true","false","true","false","true","true"))
add("logicas","cortocircuito",'''
function side(n: integer): boolean { print(n); return true; }
print(false && side(1)); print(true || side(2)); print(true && side(3));''', L("false","true",3,"true"))
add("logicas","precedencia_y_or",'''
print(true || false && false); print((true || false) && false); print(!false && !false);''', L("true","false","true"))
add("logicas","floats_comparaciones",'''
let a: float = 1.5; let b: float = 2.5; let two: integer = 2;
print(a < b); print(b <= b); print(b > a); print(a == a); print(a != b); print(two < b); print(b >= 3.0);''', L("true","true","true","true","true","true","false"))
add("logicas","strings_contenido",'''
let p: string = "a"; let q: string = p + "bc";
print(q); print(q == "abc"); print(q != "abc"); print("x" != "y");''', L("abc","true","false","true"))
add("logicas","condiciones_anidadas",'''
let a: integer = 1; let b: integer = 2; let c: integer = 3; let e: boolean = false;
if (a < b && (c < a || !e)) { print("si"); } else { print("no"); }
if (a > b || (c > a && e)) { print("si"); } else { print("no"); }''', L("si","no"))
add("logicas","booleano_en_variable_y_parametro",'''
function f(a: boolean, n: integer, b: boolean): boolean { return a && b || n > 5; }
let t: boolean = true; let u: boolean = false;
print(f(t, 1, u)); print(f(t, 9, u)); print(f(t, 1, t));''', L("false","true","true"))

# ---------------- arreglos
add("arreglos","suma_y_escritura",'''
let a: integer[] = [1, 2, 3]; a[1] = 20; print(a[0] + a[1] + a[2]);''', L(24))
add("arreglos","matriz",'''
let m = [[1, 2], [3, 4]]; let i: integer = 1; let j: integer = 0; m[0][1] = 7; m[i][j] = m[j][i] + 1; print(m[0][1]); print(m[1][0]); print(m[1][1]);''', L(7,8,4))
add("arreglos","tipos_float_string_bool",'''
let f: float[] = [1.5, 2.5]; let s: string[] = ["a", "b"]; let b: boolean[] = [true, false];
print(f[0] + f[1]); print(s[1]); print(b[1]); f[0] = 3; print(f[0]);''', L(4.0,"b","false",3.0))
add("arreglos","escribir_en_ciclo",'''
let a: integer[] = [0, 0, 0, 0, 0]; let t: integer = 0;
for (let k: integer = 0; k < 5; k = k + 1) { a[k] = k * k; }
foreach (v in a) { t = t + v; } print(t);''', L(30))
add("arreglos","referencia_compartida_en_funcion",'''
function fill(a: integer[]) { a[0] = 99; }
function mk(): integer[] { return [4, 5, 6]; }
let a: integer[] = [1, 2]; fill(a); print(a[0]); let b = mk(); print(b[2]);''', L(99,6))
add("arreglos","fuera_de_rango_atrapado",'''
let a: integer[] = [1, 2, 3];
try { print(a[5]); } catch (e) { print(e); }
try { let i: integer = -1; print(a[i]); } catch (e) { print(e); }
try { a[3] = 1; } catch (e) { print(e); }
print(a[2]);''', L("indice fuera de rango","indice fuera de rango","indice fuera de rango",3))
add("arreglos","fuera_de_rango_sin_catch",'''
let a: integer[] = [1]; print("antes"); print(a[1]); print("despues");''', ("has","Excepcion no capturada: indice fuera de rango"))
add("arreglos","arreglo_vacio_y_foreach",'''
let a: integer[] = []; let n: integer = 0; foreach (v in a) { n = n + 1; } print(n);''', L(0))
add("arreglos","arreglo_de_arreglos_desiguales",'''
let a = [[1], [2, 3], [4, 5, 6]]; print(a[2][2]); print(a[1][1]); print(a[0][0]);''', L(6,3,1))
add("arreglos","indice_calculado",'''
let a: integer[] = [10, 20, 30, 40]; let i: integer = 1; print(a[i + 2]); print(a[i * 2]); print(a[a[0] / 10]);''', L(40,30,20))

# ---------------- control de flujo
add("control_flujo","if_else_anidado",'''
let x: integer = 7;
if (x < 5) { print("chico"); } else { if (x < 10) { print("mediano"); } else { print("grande"); } }''', L("mediano"))
add("control_flujo","while_break_continue",'''
let i: integer = 0;
while (true) { i = i + 1; if (i == 3) { continue; } if (i > 5) { break; } print(i); }''', L(1,2,4,5))
add("control_flujo","do_while",'''
let n: integer = 3; do { n = n - 1; if (n == 1) { continue; } print(n); } while (n > 0);''', L(2,0))
add("control_flujo","for_continue_break",'''
for (let k: integer = 0; k < 10; k = k + 1) { if (k % 2 == 0) { continue; } if (k > 7) { break; } print(k); }''', L(1,3,5,7))
add("control_flujo","foreach_break_continue",'''
let notas: integer[] = [90, 50, 100, 70];
foreach (n in notas) { if (n < 60) { continue; } if (n == 100) { break; } print(n); }''', L(90))
add("control_flujo","switch_caida_y_default",'''
let d: integer = 1;
switch (d) { case 1: print("lunes"); case 2: print("martes"); default: print("otro"); }
switch (3) { case 1: print("uno"); break; case 2: print("dos"); break; }
print("fin");''', L("lunes","martes","otro","fin"))
add("control_flujo","switch_strings_y_expresion",'''
let s: string = "b";
switch (s) { case "a": print("A"); break; case "b": print("B"); break; default: print("?"); }
let k: integer = 0;
switch (k + 1) { case 0: k = 10; break; default: k = k + 1; }
print(k);''', L("B",1))
add("control_flujo","break_solo_del_ciclo_interno",'''
let c: integer = 0;
for (let i: integer = 0; i < 3; i = i + 1) { for (let j: integer = 0; j < 3; j = j + 1) { if (j == 1) { break; } c = c + 1; } }
print(c);''', L(3))
add("control_flujo","mil_iteraciones",'''
let s: integer = 0; let i: integer = 1; while (i <= 1000) { s = s + i; i = i + 1; } print(s);''', L(500500))
add("control_flujo","while_false_y_for_vacio",'''
let n: integer = 0; while (false) { n = 1; } for (let i: integer = 5; i < 5; i = i + 1) { n = 2; } print(n);''', L(0))
add("control_flujo","if_con_condicion_float_y_string",'''
let f: float = 1.5; let s: string = "x";
if (f > 1.0) { print("a"); } if (s == "x") { print("b"); } if (s != "x") { print("c"); } else { print("d"); }''', L("a","b","d"))
add("control_flujo","switch_dentro_de_ciclo_con_break",'''
for (let i: integer = 0; i < 4; i = i + 1) { switch (i) { case 1: print("uno"); break; case 2: continue; default: print(i); } }''', L(0,"uno",3))

# ---------------- funciones
add("funciones","ocho_argumentos",'''
function s(a: integer, b: integer, c: integer, d: integer, e: integer, f: integer, g: integer, h: integer): integer { return a + b + c + d + e + f + g + h; }
print(s(1, 2, 3, 4, 5, 6, 7, 8));''', L(36))
add("funciones","mezcla_float_int",'''
function mix(a: integer, x: float, b: integer, y: float): float { return x * a + y * b; }
print(mix(2, 1.5, 3, 0.5));''', L(4.5))
add("funciones","retorno_temprano_y_void",'''
function m(n: integer) { if (n < 0) { print("neg"); return; } print(n); }
m(-1); m(5);''', L("neg",5))
add("funciones","llamadas_anidadas_en_argumentos",'''
function add(a: integer, b: integer): integer { return a + b; }
print(add(add(1, 2), add(3, 4)));''', L(10))
add("funciones","temporales_vivos_durante_llamada",'''
function f(x: integer): integer { return x + 1; }
let r: integer = 1 + f(2) * (3 + f(4)); print(r);''', L(25))
add("funciones","retorna_string_bool_float",'''
function s(): string { return "hola"; } function b(x: integer): boolean { return x > 2; } function f(): float { return 2; }
print(s()); print(b(3)); print(b(1)); print(f());''', L("hola","true","false",2.0))
add("funciones","funcion_anidada",'''
function ext(n: integer): integer { function int(m: integer): integer { return m + 1; } return int(n) * 2; }
print(ext(3));''', L(8))
add("funciones","modifica_global_y_sombrea",'''
let g: integer = 1;
function f() { g = g + 10; let g2: integer = 5; g = g + g2; }
f(); f(); print(g);''', L(31))
add("funciones","closure_contador",'''
function mk(): integer {
  let c: integer = 0;
  function inc(): integer { c = c + 1; return c; }
  inc(); inc(); return inc();
}
print(mk());''', L(3))
add("funciones","funcion_sin_return_usada_como_sentencia",'''
function nada() { } nada(); nada(); print("ok");''', L("ok"))
add("funciones","parametros_modificados_no_afectan_al_llamador",'''
function f(a: integer): integer { a = a + 1; return a; }
let x: integer = 5; print(f(x)); print(x);''', L(6,5))
add("funciones","string_concat_en_argumento",'''
function sh(s: string) { print(s); } sh("a" + "b" + "c");''', L("abc"))

# ---------------- recursividad
add("recursividad","factorial_y_fibonacci",'''
function fact(n: integer): integer { if (n <= 1) { return 1; } return n * fact(n - 1); }
function fib(n: integer): integer { if (n < 2) { return n; } return fib(n - 1) + fib(n - 2); }
print(fact(10)); print(fib(20));''', L(3628800,6765))
add("recursividad","mutua",'''
function par(n: integer): boolean { if (n == 0) { return true; } return impar(n - 1); }
function impar(n: integer): boolean { if (n == 0) { return false; } return par(n - 1); }
print(par(10));''', L("true"))
add("recursividad","profundidad_20000",'''
function s(n: integer): integer { if (n == 0) { return 0; } return n + s(n - 1); }
print(s(20000));''', L(200010000))
add("recursividad","ackermann_hanoi_gcd",'''
function ack(m: integer, n: integer): integer {
  if (m == 0) { return n + 1; } if (n == 0) { return ack(m - 1, 1); } return ack(m - 1, ack(m, n - 1)); }
function han(n: integer): integer { if (n == 0) { return 0; } return 2 * han(n - 1) + 1; }
function gcd(a: integer, b: integer): integer { if (b == 0) { return a; } return gcd(b, a % b); }
print(ack(2, 3)); print(han(10)); print(gcd(48, 18));''', L(9,1023,6))
add("recursividad","float_y_arreglo",'''
function pw(b: float, e: integer): float { if (e == 0) { return 1.0; } return b * pw(b, e - 1); }
function sum(a: integer[], i: integer): integer { if (i < 0) { return 0; } return a[i] + sum(a, i - 1); }
print(pw(2.0, 10)); print(sum([1, 2, 3, 4], 3));''', L(1024.0,10))
add("recursividad","locales_independientes_por_activacion",'''
function f(n: integer): integer { let x: integer = n * 10; if (n > 0) { let y: integer = f(n - 1); return x + y; } return x; }
print(f(3));''', L(60))
add("recursividad","string_y_bool_recursivo",'''
function rep(s: string, n: integer): string { if (n == 0) { return ""; } return s + rep(s, n - 1); }
print(rep("ab", 3));''', L("ababab"))

# ---------------- clases
add("clases","punto_basico",'''
class Punto { var x: integer = 0; var y: integer = 0;
  function constructor(a: integer, b: integer) { this.x = a; this.y = b; }
  function sumar(): integer { return this.x + this.y; } }
let p = new Punto(3, 4); print(p.x); p.y = p.x + 1; print(p.sumar());''', L(3,7))
add("clases","metodo_llama_metodo",'''
class C { var n: integer = 2; function dob(): integer { return this.n * 2; } function cuad(): integer { return this.dob() * this.dob(); } }
let c = new C(); print(c.cuad());''', L(16))
add("clases","lista_enlazada",'''
class Nodo { var v: integer; var sig: Nodo; function constructor(x: integer) { this.v = x; this.sig = null; } }
let a = new Nodo(1); let b = new Nodo(2); let c = new Nodo(3); a.sig = b; b.sig = c;
let t: integer = 0; let cur: Nodo = a;
while (cur != null) { t = t + cur.v; cur = cur.sig; } print(t);''', L(6))
add("clases","campos_booleanos_contiguos",'''
class F { var a: boolean = true; var b: boolean = false; var n: integer = 7; var c: boolean = true; var s: string = "ok"; }
let f = new F(); print(f.a); print(f.b); print(f.n); print(f.c); print(f.s); f.b = true; f.n = 9; print(f.b); print(f.n); print(f.a);''', L("true","false",7,"true","ok","true",9,"true"))
add("clases","campos_float_y_mezcla",'''
class V { var x: float = 1.5; var n: integer = 2; function esc(k: float): float { return this.x * k + this.n; } }
let v = new V(); print(v.esc(2.0)); v.x = 4; print(v.x);''', L(5.0,4.0))
add("clases","estado_independiente_por_instancia",'''
class Ctr { var n: integer = 0; function inc() { this.n = this.n + 1; } function get(): integer { return this.n; } }
let a = new Ctr(); let b = new Ctr(); a.inc(); a.inc(); b.inc(); print(a.get()); print(b.get());''', L(2,1))
add("clases","objeto_a_funcion_y_arreglo_de_objetos",'''
class P { var v: integer = 1; }
function bump(p: P) { p.v = p.v + 10; }
let a: P[] = [new P(), new P()]; bump(a[1]); bump(a[1]); print(a[0].v); print(a[1].v);''', L(1,21))
add("clases","null_atrapado",'''
class N { var v: integer = 1; function m(): integer { return 1; } }
let n: N = null;
try { print(n.v); } catch (e) { print(e); }
try { print(n.m()); } catch (e) { print(e); }
try { n.v = 2; } catch (e) { print(e); }''', L("referencia nula","referencia nula","referencia nula"))
add("clases","constante_y_arreglo_en_campo",'''
class K { const V: string = "1.0"; var a: integer[] = [1, 2, 3]; function s(): integer { return this.a[0] + this.a[2]; } }
let k = new K(); print(k.V); print(k.s()); k.a[1] = 50; print(k.a[1]);''', L("1.0",4,50))
add("clases","constructor_con_float_y_string",'''
class P { var n: string; var h: float; function constructor(n: string, h: float) { this.n = n; this.h = h; } function d(): string { return this.n + "!"; } }
let p = new P("ana", 1.75); print(p.d()); print(p.h);''', L("ana!",1.75))
# ---------------- herencia
HERENCIA = '''
class Animal { var nombre: string; function constructor(n: string) { this.nombre = n; }
  function hablar(): string { return "..."; } function describir(): string { return this.nombre + ":" + this.hablar(); } }
class Perro : Animal { var raza: string = "criollo"; function hablar(): string { return "guau"; } }
class Gato : Animal { function hablar(): string { return "miau"; } }
'''
add("herencia","override_y_heredado",HERENCIA+'''
let p = new Perro("rex"); print(p.hablar()); print(p.describir()); print(p.raza); p.nombre = "max"; print(p.describir());''', L("guau","rex:guau","criollo","max:guau"))
add("herencia","polimorfismo_por_variable_base",HERENCIA+'''
let a: Animal = new Perro("a"); let b: Animal = new Gato("b"); let c: Animal = new Animal("c");
print(a.hablar()); print(b.hablar()); print(c.hablar()); print(a.describir()); print(b.describir());
a = b; print(a.hablar());''', L("guau","miau","...","a:guau","b:miau","miau"))
add("herencia","funcion_recibe_base",HERENCIA+'''
function f(x: Animal): string { return x.hablar(); }
print(f(new Perro("p"))); print(f(new Gato("g"))); print(f(new Animal("a")));''', L("guau","miau","..."))
add("herencia","cadena_de_tres_y_cuatro",'''
class A { var a: integer = 1; function q(): string { return "A"; } function r(): integer { return this.a; } }
class B : A { var b: integer = 2; function q(): string { return "B"; } }
class C : B { var c: integer = 3; function s(): integer { return this.a + this.b + this.c; } }
class D : C { var d: integer = 4; function q(): string { return "D"; } function s(): integer { return 100 + this.d; } }
let c = new C(); let d = new D();
print(c.q()); print(c.s()); print(d.q()); print(d.s()); print(d.r()); print(d.a + d.b + d.c + d.d);''', L("B",6,"D",104,1,10))
add("herencia","padre_llama_metodo_sobrescrito_via_this",'''
class A { function g(): string { return "A"; } function f(): string { return this.g(); } }
class B : A { function g(): string { return "B"; } }
let b = new B(); let a = new A(); print(b.f()); print(a.f());''', L("B","A"))
add("herencia","campos_padre_con_bool_y_hijo",'''
class P { var x: boolean = true; var n: integer = 5; var y: boolean = false; }
class H : P { var z: boolean = true; var m: integer = 6; function t(): integer { return this.n + this.m; } }
let h = new H(); print(h.x); print(h.y); print(h.z); print(h.n); print(h.m); print(h.t()); h.y = true; h.n = 50; print(h.y); print(h.t());''', L("true","false","true",5,6,11,"true",56))
add("herencia","hijo_modifica_campo_heredado",'''
class A { var v: integer = 1; function get(): integer { return this.v; } }
class B : A { function set(x: integer) { this.v = x; } }
let b = new B(); b.set(42); print(b.get()); print(b.v);''', L(42,42))
add("herencia","constructor_heredado_y_propio",'''
class A { var n: integer; function constructor(x: integer) { this.n = x; } }
class B : A { }
class C : A { var m: integer = 9; function constructor(x: integer) { this.n = x + 1; } }
let b = new B(7); let c = new C(7); print(b.n); print(c.n); print(c.m);''', L(7,8,9))
add("herencia","arreglo_homogeneo_de_hijos",HERENCIA+'''
let ps: Perro[] = [new Perro("a"), new Perro("b")]; print(ps[1].hablar()); print(ps[0].describir());''', L("guau","a:guau"))
add("herencia","arreglo_mixto_de_subclases",HERENCIA+'''
let zoo: Animal[] = [new Perro("a"), new Gato("b")]; print(zoo[0].hablar()); print(zoo[1].hablar());''', L("guau","miau"))
add("herencia","override_con_float_y_args",'''
class F { function area(k: float): float { return k; } }
class G : F { function area(k: float): float { return k * 2.0; } }
let x: F = new G(); print(x.area(1.5)); let y: F = new F(); print(y.area(1.5));''', L(3.0,1.5))
add("herencia","metodo_nuevo_solo_en_hijo_y_override_medio",'''
class A { function w(): string { return "A"; } }
class B : A { function w(): string { return "B"; } function solo(): string { return "solo"; } }
class C : B { }
let c = new C(); print(c.w()); print(c.solo());''', L("B","solo"))

# ---------------- try/catch
add("try_catch","basico_y_flujo_normal",'''
let a: integer[] = [1];
try { print(a[0]); } catch (e) { print("no"); }
try { print(a[2]); } catch (e) { print(e); }
print("fin");''', L(1,"indice fuera de rango","fin"))
add("try_catch","anidado",'''
let a: integer[] = [1];
try { try { print(a[9]); } catch (e) { print("interno"); print(a[8]); } print("no llega"); } catch (e2) { print("externo"); }
print("fin");''', L("interno","externo","fin"))
add("try_catch","excepcion_en_funcion_llamada_desde_try",'''
function f(a: integer[], i: integer): integer { return a[i]; }
function g(a: integer[]): integer { return f(a, 7) + 1; }
let a: integer[] = [1, 2];
try { print(g(a)); } catch (e) { print(e); }
print(f(a, 1));''', L("indice fuera de rango",2))
add("try_catch","valores_previos_se_conservan",'''
let x: integer = 1; let a: integer[] = [1];
try { x = 2; print(a[3]); x = 3; } catch (e) { print(x); }
print(x);''', L(2,2))
add("try_catch","en_ciclo_con_break_continue",'''
let a: integer[] = [1, 2];
for (let i: integer = 0; i < 5; i = i + 1) {
  try { if (i == 1) { continue; } if (i == 4) { break; } print(a[i]); } catch (e) { print("x"); }
}''', L(1,"x","x"))
add("try_catch","excepcion_dentro_de_recursion",'''
function f(a: integer[], n: integer): integer { if (n == 0) { return a[10]; } return f(a, n - 1) + 1; }
let a: integer[] = [1];
try { print(f(a, 50)); } catch (e) { print(e); }
try { print(f(a, 3)); } catch (e) { print(e); } print("ok");''', L("indice fuera de rango","indice fuera de rango","ok"))
add("try_catch","try_dentro_de_funcion_recursiva",'''
function f(a: integer[], n: integer): integer {
  if (n == 0) { return 0; }
  try { return a[n] + f(a, n - 1); } catch (e) { return 100; }
}
let a: integer[] = [0, 1, 2, 3];
print(f(a, 3)); print(f(a, 6));''', L(6,100))
add("try_catch","catch_con_string_y_variables_locales",'''
function f(): string {
  let a: integer[] = []; let msg: string = "pre";
  try { print(a[0]); } catch (err) { msg = msg + ":" + err; }
  return msg;
}
print(f());''', L("pre:indice fuera de rango"))
add("try_catch","objeto_null_y_arreglo_neg",'''
class N { var v: integer = 1; }
function t(n: N): integer { try { return n.v; } catch (e) { return -1; } }
print(t(new N())); print(t(null));
try { let a = [1]; print(a[0 - 1]); } catch (e) { print(e); }''', L(1,-1,"indice fuera de rango"))
add("try_catch","metodo_con_try_y_campos",'''
class S { var a: integer[] = [1, 2]; var n: integer = 0;
  function leer(i: integer): integer { try { this.n = this.n + 1; return this.a[i]; } catch (e) { return -1; } } }
let s = new S(); print(s.leer(1)); print(s.leer(9)); print(s.n);''', L(2,-1,2))

# ---------------- raros
add("raros","trece_valores_vivos",'''
let a: integer = 1; let b: integer = 2; let c: integer = 3; let d: integer = 4; let e: integer = 5; let f: integer = 6; let g: integer = 7;
let h: integer = 8; let i: integer = 9; let j: integer = 10; let k: integer = 11; let l: integer = 12; let m: integer = 13;
print(a + b + c + d + e + f + g + h + i + j + k + l + m);
print((a + b) * (c + d) * (e + f) - (g + h) * (i + j));''', L(91,3*7*11-15*19))
add("raros","concat_en_ciclo",'''
let s: string = ""; for (let i: integer = 0; i < 5; i = i + 1) { s = s + "x"; } print(s);''', L("xxxxx"))
add("raros","misma_variable_dos_veces_y_swap",'''
let x: integer = 6; print(x * x); let y: integer = 9; let t: integer = x; x = y; y = t; print(x); print(y);''', L(36,9,6))
add("raros","negativos_y_ceros",'''
let n: integer = -1; let z: integer = 0; print(n < 0); print(z == 0); print(n > z); print(z >= 0); print(n <= -1);''', L("true","true","false","true","true"))
add("raros","expresion_profunda",'''
let a: integer = 1;
print(((((((((((a + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1);
print(1 + (2 + (3 + (4 + (5 + (6 + (7 + (8 + (9 + a)))))))));''', L(12,46))
add("raros","float_en_varios_contextos",'''
function h(x: float): float { return x / 2; }
let f: float = 3; let a: float[] = [1, 2.5]; class Q { var z: float = 1; }
let q = new Q(); print(f); print(a[0]); print(q.z); print(h(5)); print(f + a[1]);''', L(3.0,1.0,1.0,2.5,5.5))
add("raros","for_con_variable_global_y_locales",'''
let total: integer = 0;
function sq(n: integer): integer { return n * n; }
for (let i: integer = 1; i <= 4; i = i + 1) { let t: integer = sq(i); total = total + t; }
print(total);''', L(30))
add("raros","bloque_vacio_y_sentencias_sueltas",'''
{ } let x: integer = 1; { { } } if (x == 1) { } else { } print(x);''', L(1))

# ---------------- estrés extra
add("estres","metodo_con_cinco_args_y_float",'''
class M { var base: integer = 100;
  function f(a: integer, b: float, c: integer, d: integer, e: float): float { return b * a + e * c + d + this.base; } }
let m = new M(); print(m.f(2, 1.5, 4, 5, 0.5));''', L(110.0))
add("estres","llamada_virtual_con_valores_vivos",'''
class A { function k(x: integer): integer { return x + 1; } }
class B : A { function k(x: integer): integer { return x * 10; } }
let a: A = new A(); let b: A = new B();
let u: integer = 2; let v: integer = 3; let w: integer = u + v;
let r: integer = w + a.k(u) * b.k(v) + u * v;
print(r);''', L(5 + 3*30 + 6))
add("estres","cadena_de_campos_y_metodos",'''
class C { var v: integer = 7; function me(): C { return this; } }
class B { var c: C; function constructor() { this.c = new C(); } function dame(): C { return this.c; } }
class A { var b: B; function constructor() { this.b = new B(); } }
let a = new A(); print(a.b.c.v); print(a.b.dame().me().v); a.b.c.v = 9; print(a.b.dame().v);''', L(7,7,9))
add("estres","cincuenta_locales",'''
function f(): integer {
  let v0: integer = 0; let v1: integer = 1; let v2: integer = 2; let v3: integer = 3; let v4: integer = 4;
  let v5: integer = 5; let v6: integer = 6; let v7: integer = 7; let v8: integer = 8; let v9: integer = 9;
  let w0: integer = 10; let w1: integer = 11; let w2: integer = 12; let w3: integer = 13; let w4: integer = 14;
  let w5: integer = 15; let w6: integer = 16; let w7: integer = 17; let w8: integer = 18; let w9: integer = 19;
  let x0: float = 0.5; let x1: float = 1.5;
  return v0 + v1 + v2 + v3 + v4 + v5 + v6 + v7 + v8 + v9 + w0 + w1 + w2 + w3 + w4 + w5 + w6 + w7 + w8 + w9;
}
print(f());''', L(190))
add("estres","arreglo_grande_y_modificacion_en_funcion_global",'''
let g: integer[] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
function set(i: integer, v: integer) { g[i] = v; }
for (let i: integer = 0; i < 10; i = i + 1) { set(i, i * 3); }
let s: integer = 0; foreach (x in g) { s = s + x; } print(s); print(g[9]);''', L(135,27))
add("estres","condicion_con_llamadas_en_while",'''
function lt(a: integer, b: integer): boolean { return a < b; }
let i: integer = 0; let s: integer = 0;
while (lt(i, 5) && lt(s, 100)) { s = s + i * 10; i = i + 1; } print(i); print(s);''', L(5,100))
add("estres","reasignar_variable_base_a_otro_tipo_hijo",HERENCIA+'''
let a: Animal = new Perro("a"); print(a.hablar()); a = new Gato("g"); print(a.hablar()); a = new Animal("z"); print(a.hablar());''', L("guau","miau","..."))
add("estres","objetos_en_recursion",'''
class T { var l: T; var r: T; var v: integer;
  function constructor(x: integer) { this.v = x; this.l = null; this.r = null; } }
function ins(t: T, x: integer): T {
  if (t == null) { return new T(x); }
  if (x < t.v) { t.l = ins(t.l, x); } else { t.r = ins(t.r, x); }
  return t; }
function suma(t: T): integer { if (t == null) { return 0; } return t.v + suma(t.l) + suma(t.r); }
function alt(t: T): integer { if (t == null) { return 0; } let a: integer = alt(t.l); let b: integer = alt(t.r); if (a > b) { return a + 1; } return b + 1; }
let raiz: T = null; let xs: integer[] = [5, 3, 8, 1, 4, 7, 9, 2, 6];
foreach (x in xs) { raiz = ins(raiz, x); } print(suma(raiz)); print(alt(raiz));''', L(45,4))
add("estres","strings_largos_y_comparacion_por_contenido",'''
let a: string = "hola"; let b: string = "ho" + "la"; let c: string = "hol";
print(a == b); print(a == c); print(a != c); print(a + b + c);
switch (b) { case "hola": print("si"); break; default: print("no"); }''', L("true","false","true","holaholahol","si"))
add("estres","valor_de_retorno_ignorado_y_encadenado",'''
function f(x: integer): integer { return x + 1; }
f(1); f(f(1)); let y: integer = f(f(f(0))); print(y);''', L(3))
add("estres","variables_globales_usadas_en_metodos",'''
let tot: integer = 0;
class A { function add(n: integer) { tot = tot + n; } }
let a = new A(); a.add(3); a.add(4); print(tot);''', L(7))
add("estres","closure_con_recursion_del_contenedor_conocido",'''
function ext(n: integer): integer {
  let x: integer = n * 10;
  function g(): integer { return x + 1; }
  if (n > 0) { let r: integer = ext(n - 1); return r + g(); }
  return g();
}
print(ext(2));''', L(11 + 21 + 1) if False else L(33))
add("estres","float_en_condiciones_y_acumulador",'''
let s: float = 0.0; let i: integer = 0;
while (s < 2.0) { s = s + 0.5; i = i + 1; } print(s); print(i);''', L(2.0,4))
add("estres","excepcion_en_metodo_virtual",'''
class A { function f(a: integer[]): integer { return a[0]; } }
class B : A { function f(a: integer[]): integer { return a[5]; } }
let x: A = new B(); let e: integer[] = [1];
try { print(x.f(e)); } catch (m) { print(m); }
let y: A = new A(); print(y.f(e));''', L("indice fuera de rango",1))
add("estres","floats_vivos_mas_que_registros",'''
let a: float = 1.0; let b: float = 2.0; let c: float = 3.0; let d: float = 4.0; let e: float = 5.0; let f: float = 6.0;
let g: float = 7.0; let h: float = 8.0; let i: float = 9.0; let j: float = 10.0;
print(a + b + c + d + e + f + g + h + i + j);
print((a + b) * (c + d) * (e + f) - (g + h) * (i + j));''', L(55.0, 231.0-285.0))
add("estres","mezcla_int_float_vivos_con_llamadas",'''
function f(x: float, n: integer): float { return x * n; }
let a: integer = 2; let b: float = 1.5; let c: integer = 3; let d: float = 0.5;
let r: float = a + b * f(d, c) + c * f(b, a) + d;
print(r);''', L(2 + 1.5*1.5 + 3*3.0 + 0.5))
add("estres","foreach_de_objetos_y_strings",'''
class P { var n: string; function constructor(x: string) { this.n = x; } }
let ps: P[] = [new P("a"), new P("b"), new P("c")]; let s: string = "";
foreach (p in ps) { s = s + p.n; } print(s);''', L("abc"))
add("estres","booleanos_como_valores_y_en_arreglos_de_objetos",'''
class F { var on: boolean = false; function flip() { this.on = !this.on; } }
let f = new F(); f.flip(); print(f.on); f.flip(); print(f.on); f.flip(); let b: boolean = f.on && true; print(b);''', L("true","false","true"))
