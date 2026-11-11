"""Pruebas unitarias de `getReg()` (`asm.regalloc`), sin simulador.

Cada prueba arma un bloque de instrucciones a mano y mira el texto emitido y
la traza de decisiones. Ver docs/proyecto3/01-contrato.md §4.
"""

from __future__ import annotations

from asm.emitter import AsmEmitter
from asm.frames import Home
from asm.ir import FLOAT, INT, Binary, Copy, Operand
from asm.regalloc import DEAD, INT_REGS, LIVE_OUT, RegAlloc, block_live_out, split_blocks


def var(name, ty=INT):
    return Operand(name, "var", ty)


def temp(n, ty=INT):
    return Operand(f"$t{n}", "temp", ty)


def const(value):
    return Operand(str(value), "const", INT, value)


class Env:
    """Un RegAlloc listo para usar sobre un bloque."""

    def __init__(self, block, live_out=None):
        self.asm = AsmEmitter()
        homes = {}

        def home(op):
            if op.key not in homes:
                homes[op.key] = Home("fp", -4 * (len(homes) + 1), 4)
            return homes[op.key]

        self.regs = RegAlloc(self.asm, home)
        self.regs.start_block(block, live_out)

    def at(self, i):
        self.regs.begin_instr(i)

    def text(self):
        return "\n".join(l.strip() for l in self.asm._text)


def test_next_use_of_temps_and_variables():
    a, t1 = var("a"), temp(1)
    block = [Binary(t1, a, "+", const(1)), Copy(var("b"), t1), Copy(var("c"), a)]
    env = Env(block)
    env.at(0)
    assert env.regs.next_use("$t1") == 1  # lo lee la instrucción siguiente
    assert env.regs.next_use("a") == 2
    env.at(1)
    assert env.regs.next_use("$t1") == DEAD  # un temporal no leído muere
    assert env.regs.next_use("b") == LIVE_OUT  # una variable nunca muere


def test_a_dead_temporary_is_never_stored_but_the_variable_it_feeds_is():
    a, t1, b = var("a"), temp(1), var("b")
    block = [Binary(t1, a, "+", const(1)), Copy(b, t1)]
    env = Env(block)
    r = env.regs
    env.at(0)
    r.use(a)
    r.def_(t1)
    r.end_instr()
    env.at(1)
    r.use(t1)
    r.def_(b)
    r.end_instr()  # aquí $t1 muere y su registro queda libre
    assert t1.key not in r.op_reg
    r.flush()
    stores = [l for l in env.text().splitlines() if l.startswith("sw")]
    home_t1 = r._home(t1).mem()
    assert not any(l.endswith(home_t1) for l in stores)  # el temporal muerto no se guarda
    assert any(l.endswith(r._home(b).mem()) for l in stores)  # la variable sí


def test_def_reuses_the_register_of_a_source_that_just_died():
    t1, t2 = temp(1), temp(2)
    block = [Binary(t1, var("a"), "+", var("b")), Binary(t2, t1, "+", const(5)), Copy(var("c"), t2)]
    env = Env(block)
    r = env.regs
    env.at(0)
    r.use(var("a")); r.use(var("b"))
    r1 = r.def_(t1)
    r.end_instr()
    env.at(1)
    src = r.use(t1)
    r2 = r.def_(t2)  # t1 muere aquí: su registro se reutiliza
    assert r2 == src == r1
    assert r.trace[-1]["reason"] == "reuso"


def test_spill_picks_the_value_with_the_farthest_next_use():
    names = [var(f"v{i}") for i in range(10)]
    extra = var("extra")
    # v0 se vuelve a usar al final; v9 enseguida: al faltar registro se expulsa v0
    block = [Copy(var(f"w{i}"), names[i]) for i in range(10)]
    block += [Copy(var("z"), extra), Copy(var("y"), names[9]), Copy(var("x"), names[0])]
    env = Env(block)
    r = env.regs
    for i in range(10):
        env.at(i)
        r.use(names[i])
        r.end_instr()
    r.locked.clear()
    env.at(10)
    r.use(extra)  # no hay registros libres -> spill
    spills = [t for t in r.trace if t["reason"] == "spill"]
    assert len(spills) == 1
    # todos los vi son variables (LIVE_OUT) salvo los que se leen después en el bloque:
    # la víctima es la de siguiente uso más lejano, no la de uso inmediato
    assert spills[0]["op"] != "v9"


def test_flush_stores_only_dirty_live_values():
    b = var("b")
    block = [Copy(b, const(5)), Copy(temp(1), const(7)), Copy(var("c"), b)]
    env = Env(block)
    r = env.regs
    env.at(0)
    rb = r.def_(b)
    r.end_instr()
    env.at(1)
    r.def_(temp(1))  # $t1 no se lee jamás: está muerto
    r.end_instr()
    env.at(2)
    r.flush()
    stores = [l for l in env.text().splitlines() if l.startswith("sw")]
    assert len(stores) == 1 and rb in stores[0]  # solo `b` (variable viva)
    # un segundo flush no repite nada
    before = len(env.asm._text)
    r.flush()
    assert len(env.asm._text) == before


def test_constants_use_zero_register_or_a_scratch():
    env = Env([Copy(var("a"), const(0))])
    env.at(0)
    assert env.regs.use(const(0)) == "$zero"
    reg = env.regs.use(const(42))
    assert reg in INT_REGS and "li    " + reg + ", 42" in env.text()
    env.regs.end_instr()
    assert env.regs.scratch_regs == []  # el scratch se libera


def test_float_values_use_the_float_register_class():
    f = Operand("f", "var", FLOAT)
    env = Env([Copy(Operand("g", "var", FLOAT), f)])
    env.at(0)
    rf = env.regs.use(f)
    assert rf.startswith("$f") and "lwc1" in env.text()
    rg = env.regs.def_(Operand("g", "var", FLOAT))
    assert rg.startswith("$f")


def test_invalidate_forgets_registers_but_never_loses_a_live_value():
    a = var("a")
    env = Env([Copy(a, const(9)), Copy(var("b"), a)])
    r = env.regs
    env.at(0)
    r.def_(a)
    r.end_instr()
    r.invalidate()  # `a` estaba sucio y vivo: se guarda antes de olvidarlo
    assert any(l.startswith("sw") for l in env.text().splitlines())
    assert r.reg_op == {} and r.op_reg == {}


def test_block_liveness_keeps_a_temporary_alive_across_blocks():
    from asm.ir import CondJump, Goto, Label
    t1 = temp(1)
    body = [
        Copy(t1, const(1)),
        CondJump("ifFalse", var("c"), None, None, "L2"),
        Copy(var("x"), const(0)),
        Goto("L3"),
        Label("L2"),
        Copy(var("y"), t1),   # $t1 se usa en un bloque posterior
        Label("L3"),
        Copy(var("z"), const(3)),
    ]
    blocks = split_blocks(body)
    live = block_live_out(blocks)
    assert "$t1" in live[0]
    assert "$t1" not in live[-1]

def _dirty_pressure_env():
    values = [temp(i + 1) for i in range(10)]
    extra = temp(11)
    block = [Copy(op, const(i + 1)) for i, op in enumerate(values)]
    block.append(Copy(extra, const(99), line="$t11 = 99"))
    # Todos siguen vivos; t10 es el de uso más lejano.
    block += [Copy(var(f"out{i}"), op) for i, op in enumerate(values)]
    block.append(Copy(var("last"), extra))
    env = Env(block)
    for i, op in enumerate(values):
        env.at(i)
        reg = env.regs.def_(op)
        env.asm.ins(f"li {reg}, {i + 1}")
        env.regs.end_instr()
    env.at(10)
    return env, values, extra


def test_dirty_spill_saves_exact_farthest_value_and_records_trace():
    env, values, extra = _dirty_pressure_env()
    r = env.regs
    victim = values[-1]
    old_reg = r.op_reg[victim.key]
    before = len(env.asm._text)
    result = r.def_(extra)
    assert result == old_reg
    emitted = [line.split() for line in env.asm._text[before:]]
    assert emitted == [["sw", old_reg + ",", r._home(victim).mem()]]
    assert victim.key not in r.op_reg
    assert r.op_reg[extra.key] == old_reg
    assert r.trace[-2:] == [
        {"instr": "$t11 = 99", "op": victim.key, "reg": old_reg, "reason": "spill"},
        {"instr": "$t11 = 99", "op": extra.key, "reg": old_reg, "reason": "spill"},
    ]


def test_avoid_protects_farthest_value_under_pressure():
    env, values, extra = _dirty_pressure_env()
    r = env.regs
    protected = r.op_reg[values[-1].key]
    victim = values[-2]
    victim_reg = r.op_reg[victim.key]
    before = len(env.asm._text)
    result = r.def_(extra, avoid=(protected,))
    assert result == victim_reg and result != protected
    assert r.op_reg[values[-1].key] == protected
    assert protected in r.dirty
    emitted = [line.split() for line in env.asm._text[before:]]
    assert emitted == [["sw", victim_reg + ",", r._home(victim).mem()]]
    assert r.trace[-2]["op"] == victim.key
    assert r.trace[-2]["reason"] == "spill"


def test_avoid_prevents_reusing_a_dead_source():
    source, target = temp(1), temp(2)
    env = Env([Copy(source, const(7)), Copy(target, source), Copy(var("out"), target)])
    r = env.regs
    env.at(0)
    r.def_(source)
    r.end_instr()
    env.at(1)
    source_reg = r.use(source)
    assert r.next_use(source.key) == DEAD
    target_reg = r.def_(target, avoid=(source_reg,))
    assert target_reg != source_reg
    assert r.op_reg[source.key] == source_reg
    assert r.trace[-1]["reason"] == "libre"
    r.end_instr()
    assert source.key not in r.op_reg
    assert r.op_reg[target.key] == target_reg
