"""Intérprete mínimo de MIPS para probar el esqueleto del generador SIN MARS.

Solo entiende el subconjunto que emiten el driver, el asignador y los
selectores de prueba de `testsel.py` (enteros, memoria, saltos, llamadas y
unos pocos `syscall`). **No reemplaza a MARS**: las pruebas de punta a punta de
cada área corren en el simulador real (`simulator.py`). Sirve para tener una
red de seguridad del núcleo (`getReg`, marcos, secuencia de llamada) mientras
los selectores de los demás no existen.
"""

from __future__ import annotations

import re
import struct


def f32(x):
    """Redondea a precisión simple (los floats de MIPS)."""
    try:
        return struct.unpack("<f", struct.pack("<f", x))[0]
    except OverflowError:
        return float("inf") if x > 0 else float("-inf")


def java_float(x):
    """Formato de `Float.toString` de Java (lo que imprime MARS en syscall 2)."""
    x = f32(x)
    if x != x: return "NaN"
    if x in (float("inf"), float("-inf")): return "Infinity" if x > 0 else "-Infinity"
    if x == 0: return "-0.0" if struct.pack("<f", x)[3] & 0x80 else "0.0"
    for p in range(1, 10):  # la representación más corta que sobrevive a float32
        t = "%.*g" % (p, x)
        if f32(float(t)) == x: break
    v = float(t)
    if 1e-3 <= abs(v) < 1e7:
        d = ("%.9f" % v).rstrip("0")
        if d.endswith("."): d += "0"
        # recortar a la precisión significativa
        return repr(v) if "e" not in repr(v) else d
    m, e = ("%.*e" % (p - 1, v)).split("e")
    if "." not in m: m += ".0"
    return "%sE%d" % (m, int(e))


def strip_comment(raw):
    """Quita el comentario `# ...` de una línea respetando las comillas."""
    inq = False; esc = False
    for i, ch in enumerate(raw):
        if inq:
            if esc: esc = False
            elif ch == "\\": esc = True
            elif ch == '"': inq = False
        elif ch == '"': inq = True
        elif ch == "#": return raw[:i].rstrip()
    return raw.rstrip()


class Sim:
    def __init__(self, lines, max_steps=2_000_000):
        self.R = {f"${i}": 0 for i in range(32)}
        for n, i in [("zero",0),("v0",2),("v1",3),("a0",4),("a1",5),("a2",6),("a3",7),("sp",29),("fp",30),("ra",31),("gp",28),("at",1)]:
            self.R["$"+n] = 0
        for i in range(10): self.R[f"$t{i}"] = 0
        for i in range(32): self.R[f"$f{i}"] = 0.0
        self.mem = {}
        self.out = []
        self.hi = self.lo = 0
        self.labels = {}; self.data_labels = {}
        self.prog = []
        self.heap = 0x10040000
        self.max_steps = max_steps
        self.fcond = False
        self.trace = False
        self.exit_code = 0
        self.load(lines)
        self.R["$sp"] = 0x7fffeffc

    def w(self, a, v):
        v &= 0xffffffff
        for i in range(4): self.mem[a+i] = (v >> (8*i)) & 0xff
    def r(self, a):
        v = sum(self.mem.get(a+i, 0) << (8*i) for i in range(4))
        return v - (1<<32) if v & 0x80000000 else v
    def b(self, a): 
        v = self.mem.get(a,0); return v-256 if v>127 else v
    def cstr(self, a):
        s=bytearray()
        while self.mem.get(a,0): s.append(self.mem[a]); a+=1
        return s.decode("utf-8", "replace")

    def load(self, lines):
        section = None; dp = 0x10010000
        pending_data = []
        text = []
        for raw in lines:
            line = strip_comment(raw)
            line = line.strip()
            if not line: continue
            if line == ".data": section = "data"; continue
            if line == ".text": section = "text"; continue
            if line.startswith(".globl"): continue
            if section == "data":
                m = re.match(r"^(\w+):\s*(.*)$", line)
                if m:
                    # como MARS: .word/.float alinean y la etiqueta de la misma línea las sigue
                    if m.group(2).strip().startswith((".word", ".float")): dp = (dp + 3) & ~3
                    self.data_labels[m.group(1)] = dp; line = m.group(2).strip()
                if not line: continue
                if line.startswith(".align"): dp = (dp + 3) & ~3; continue
                if line.startswith(".asciiz"):
                    lit = re.search(r'"(.*)"', line).group(1).encode().decode("unicode_escape")
                    for ch in lit.encode(): self.mem[dp] = ch; dp += 1
                    self.mem[dp] = 0; dp += 1
                elif line.startswith(".float"):
                    dp = (dp+3)&~3
                    val = float(line.split()[1]); self.w(dp, struct.unpack("<I", struct.pack("<f", val))[0]); dp += 4
                elif line.startswith(".space"):
                    dp += int(line.split()[1])
                elif line.startswith(".word"):
                    dp = (dp+3)&~3
                    for item in line[5:].split(","):
                        pending_data.append((dp, item.strip())); dp += 4
            elif section == "text":
                m = re.match(r"^([\w$.]+):\s*(.*)$", line)
                if m and not line.startswith('"'):
                    self.labels[m.group(1)] = len(text); line = m.group(2).strip()
                if line: text.append(line)
        self.code_addr = {n: 0x00400000 + 4*i for n, i in self.labels.items()}
        self.addr_code = {v: k for k, v in self.code_addr.items()}
        for addr, item in pending_data:  # un `.word etiqueta` guarda su dirección
            self.w(addr, self.data_labels.get(item, int(item) if item.lstrip("-").isdigit() else self.code_addr.get(item, 0)))
        self.prog = text
        self.pc = self.labels["main"]

    def val(self, tok):
        tok = tok.strip()
        if tok in self.R: return self.R[tok]
        if tok in self.data_labels: return self.data_labels[tok]
        if tok in self.code_addr: return self.code_addr[tok]
        return int(tok, 0)

    def ea(self, tok):
        m = re.match(r"^(-?\d+)\((\$\w+)\)$", tok.strip())
        if m: return int(m.group(1)) + self.R[m.group(2)]
        return self.data_labels[tok.strip()]

    def run(self):
        steps = 0
        R = self.R
        while True:
            steps += 1
            if steps > self.max_steps: raise RuntimeError("demasiados pasos (¿ciclo infinito?)")
            line = self.prog[self.pc]; self.pc += 1
            if self.trace: print(f"{self.pc-1:4d} {line:34s} f0={R['$f0']} f4={R['$f4']} f6={R['$f6']} f12={R['$f12']} v0={R['$v0']}")
            parts = line.split(None, 1)
            op = parts[0]; args = [a.strip() for a in re.split(r",\s*", parts[1])] if len(parts) > 1 else []
            R["$zero"] = 0
            if op == "li": R[args[0]] = self.val(args[1])
            elif op == "la": R[args[0]] = self.val(args[1])
            elif op == "move": R[args[0]] = R[args[1]]
            elif op == "mov.s": R[args[0]] = R[args[1]]
            elif op == "lw": R[args[0]] = self.r(self.ea(args[1]))
            elif op == "sw": self.w(self.ea(args[1]), R[args[0]])
            elif op == "lb": R[args[0]] = self.b(self.ea(args[1]))
            elif op == "sb": self.mem[self.ea(args[1])] = R[args[0]] & 0xff
            elif op == "lwc1": R[args[0]] = struct.unpack("<f", struct.pack("<I", self.r(self.ea(args[1])) & 0xffffffff))[0]
            elif op == "swc1": self.w(self.ea(args[1]), struct.unpack("<I", struct.pack("<f", R[args[0]]))[0])
            elif op == "l.s":
                a = self.data_labels[args[1]] if args[1] in self.data_labels else self.ea(args[1])
                R[args[0]] = struct.unpack("<f", struct.pack("<I", self.r(a) & 0xffffffff))[0]
            elif op in ("addu","add"): R[args[0]] = self.s32(R[args[1]] + R[args[2]])
            elif op in ("subu","sub"): R[args[0]] = self.s32(R[args[1]] - R[args[2]])
            elif op == "mul": R[args[0]] = self.s32(R[args[1]] * R[args[2]])
            elif op == "addiu" or op == "addi": R[args[0]] = self.s32(R[args[1]] + int(args[2]))
            elif op == "div":
                a, b = R[args[0]], R[args[1]]
                q = abs(a)//abs(b) * (1 if (a<0)==(b<0) else -1); self.lo = q; self.hi = a - q*b
            elif op == "mflo": R[args[0]] = self.lo
            elif op == "mfhi": R[args[0]] = self.hi
            elif op == "slt": R[args[0]] = int(R[args[1]] < self.rv(args[2]))
            elif op == "sgt": R[args[0]] = int(R[args[1]] > self.rv(args[2]))
            elif op == "sle": R[args[0]] = int(R[args[1]] <= self.rv(args[2]))
            elif op == "sge": R[args[0]] = int(R[args[1]] >= self.rv(args[2]))
            elif op == "seq": R[args[0]] = int(R[args[1]] == self.rv(args[2]))
            elif op == "sne": R[args[0]] = int(R[args[1]] != self.rv(args[2]))
            elif op == "xori": R[args[0]] = R[args[1]] ^ int(args[2])
            elif op in ("beq","bne","blt","ble","bgt","bge"):
                a, b = R[args[0]], self.rv(args[1])
                if {"beq":a==b,"bne":a!=b,"blt":a<b,"ble":a<=b,"bgt":a>b,"bge":a>=b}[op]: self.pc = self.labels[args[2]]
            elif op == "j": self.pc = self.labels[args[0]]
            elif op == "jal": R["$ra"] = self.code_addr_of(self.pc); self.pc = self.labels[args[0]]
            elif op == "jalr": R["$ra"] = self.code_addr_of(self.pc); self.pc = self.pc_of(R[args[0]])
            elif op == "jr": self.pc = self.pc_of(R[args[0]])
            elif op == "sll": R[args[0]] = self.s32(R[args[1]] << int(args[2]))
            elif op == "srl": R[args[0]] = self.s32((R[args[1]] & 0xffffffff) >> int(args[2]))
            elif op == "sltu": R[args[0]] = int((R[args[1]] & 0xffffffff) < (self.rv(args[2]) & 0xffffffff))
            elif op == "sltiu": R[args[0]] = int((R[args[1]] & 0xffffffff) < (int(args[2]) & 0xffffffff))
            elif op == "slti": R[args[0]] = int(R[args[1]] < int(args[2]))
            elif op == "bgeu":
                if (R[args[0]] & 0xffffffff) >= (self.rv(args[1]) & 0xffffffff): self.pc = self.labels[args[2]]
            elif op in ("bltz","blez","bgtz","bgez"):
                a = R[args[0]]
                if {"bltz":a<0,"blez":a<=0,"bgtz":a>0,"bgez":a>=0}[op]: self.pc = self.labels[args[1]]
            elif op in ("add.s","sub.s","mul.s","div.s"):
                x, y = R[args[1]], R[args[2]]
                R[args[0]] = f32({"add.s":x+y,"sub.s":x-y,"mul.s":x*y,"div.s":(x/y if y else float("inf"))}[op])
            elif op == "neg.s": R[args[0]] = -R[args[1]]
            elif op == "mtc1": R[args[1]] = struct.unpack("<f", struct.pack("<I", R[args[0]] & 0xffffffff))[0]
            elif op == "cvt.s.w":
                bits = struct.unpack("<I", struct.pack("<f", R[args[1]]))[0]
                R[args[0]] = f32(float(self.s32(bits)))
            elif op in ("c.lt.s","c.le.s","c.eq.s"):
                x, y = R[args[0]], R[args[1]]
                self.fcond = {"c.lt.s":x<y,"c.le.s":x<=y,"c.eq.s":x==y}[op]
            elif op == "bc1t":
                if self.fcond: self.pc = self.labels[args[0]]
            elif op == "bc1f":
                if not self.fcond: self.pc = self.labels[args[0]]
            elif op == "syscall":
                v = R["$v0"]
                if v == 1: self.out.append(str(R["$a0"]))
                elif v == 4: self.out.append(self.cstr(R["$a0"]))
                elif v == 11: self.out.append(chr(R["$a0"]))
                elif v == 2: self.out.append(java_float(R["$f12"]))
                elif v == 9: R["$v0"] = self.heap; self.heap += (R["$a0"]+3)&~3
                elif v == 10: return "".join(self.out)
                elif v == 17: self.exit_code = R["$a0"]; return "".join(self.out)
                else: raise RuntimeError(f"syscall {v}")
            else: raise RuntimeError(f"instrucción no soportada: {line}")
    def rv(self, tok): return self.R[tok] if tok in self.R else int(tok)
    @staticmethod
    def s32(v): v &= 0xffffffff; return v-(1<<32) if v & 0x80000000 else v
    def code_addr_of(self, idx): return 0x00400000 + 4*idx
    def pc_of(self, addr): return (addr - 0x00400000)//4
