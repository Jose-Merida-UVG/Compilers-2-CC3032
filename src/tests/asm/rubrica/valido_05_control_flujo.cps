let r: integer = 0;
for (let i: integer = 0; i < 4; i = i + 1) {
  for (let j: integer = 0; j < 4; j = j + 1) {
    if (j == 2) { continue; }
    if (i == 3) { break; }
    r = r + i * 10 + j;
  }
}
print(r);
let d: integer = 5; do { d = d - 2; } while (d > 0); print(d);
switch (r) { case 1: print("uno"); break; case 52: print("52"); case 99: print("cae"); break; default: print("def"); }
switch (7) { case 1: print("a"); default: print("d"); }
let q: integer = 0;
foreach (v in [1, 2, 3, 4]) { if (v % 2 == 0) { continue; } q = q + v; } print(q);
while (true) { q = q + 1; if (q > 6) { break; } } print(q);
