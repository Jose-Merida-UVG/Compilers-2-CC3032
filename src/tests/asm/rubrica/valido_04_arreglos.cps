let a: integer[] = [3, 1, 2];
print(a[0] + a[2]); a[1] = a[0] * 10; print(a[1]);
let m: integer[][] = [[1, 2], [3, 4, 5]];
print(m[1][2]); m[0][1] = 9; print(m[0][0] + m[0][1]);
let s: string[] = ["x", "y"]; s[0] = s[0] + s[1]; print(s[0]);
let i: integer = 0; let sum: integer = 0;
while (i < 3) { sum = sum + a[i]; i = i + 1; } print(sum);
let f: float[] = [1.5, 2.5]; print(f[0] + f[1]);
foreach (row in m) { foreach (v in row) { sum = sum + v; } } print(sum);
