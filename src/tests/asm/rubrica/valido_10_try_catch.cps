function pos(a: integer[], i: integer): integer { return a[i]; }
try { print(pos([1, 2], 1)); print(pos([1], 5)); print("no"); } catch (e) { print("c1"); }
try { try { print(pos([1], 5)); } catch (e) { print("interno"); print(pos([1], -1)); } } catch (e2) { print("externo"); }
function f(i: integer): integer { try { return pos([7, 8], i); } catch (e) { return -1; } }
print(f(1)); print(f(9));
for (let i: integer = 0; i < 4; i = i + 1) { try { if (i == 1) { continue; } if (i == 3) { break; } print(i); } catch (e) { print("x"); } }
class N { var v: integer; }
let n: N = null;
try { print(n.v); } catch (e) { print("nulo"); }
function rec(k: integer): integer { try { if (k == 0) { return pos([1], 3); } return rec(k - 1); } catch (e) { return k; } }
print(rec(3));
print("fin");
