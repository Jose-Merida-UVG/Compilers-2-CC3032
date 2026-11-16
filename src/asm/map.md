# MIPS backend map

Read this first, then open the files in the order below. Each file also has a
short docstring at the top.

## What goes in, what comes out

```
TAC (list of strings)  ┐
symbol table (JSON)    ┘──▶ generate_asm() ──▶ AsmResult
                                                 .lines          raw MIPS (peephole runs later)
                                                 .activation     frames + call tree, for the IDE
                                                 .regalloc_trace getReg decisions, for the IDE
```

Both inputs come from Project 2 and are only produced when the program has no
errors. The compiler never looks at the syntax tree here.

### The symbol table, in one picture

A tree of scopes. Every `{ }` and every function/class is a node.

```
GLOBAL                         symbols: functions, global variables (address gp+N)
 ├ frame {...}                 sizes of __main (the loose top-level code)
 ├ FUNCTION f                  symbols: parameters (address fp+8, fp+12, ...)
 │   ├ frame {params_size, locals_size, temps, temps_size, saved_size, total_size}
 │   └ BLOCK                   symbols: locals (address fp-4, fp-8, ...)
 │       └ BLOCK ...           nested blocks keep numbering where the parent stopped
 └ CLASS A                     layout {size, parent, fields[name, offset, size], vtable[slot, label]}
     └ FUNCTION m ...          methods are functions with `this` as parameter 0
```

Each symbol: `name, kind, type ("integer", "float[]", "(integer) -> integer"),
size, offset, address, tac_name`. The P2 computes every size and offset
(`src/semantic/layout.py`); the backend only reads them.

### `$gp` and `$fp`

- `$gp` points to the globals area. It never changes. Globals are `N($gp)`.
- `$fp` points to the current function's frame. It changes on every call.
  Parameters are above it (`fp+8...`), locals and temporaries below it.
- Object fields are `offset(object)`. Offset 0 holds the method table.

Everything is addressed from `$fp`/`$gp`, never `$sp`, because `$sp` moves while
arguments are pushed.

## Reading order

| # | File | What it does | Read |
|---|------|--------------|------|
| 1 | `generator.py` | The coordinator. `generate_asm` calls the parser, then walks every function, splits it into basic blocks and hands each instruction to its selector. Decides *when* registers are flushed to memory. | bottom first (`generate_asm`), then `run`, `_gen_function` |
| 2 | `ir/` | The TAC as Python objects: `Operand` (a value with a type), `Ty`, `Instr` and one class per instruction (`Binary`, `Call`, ...). Each instruction declares `READS`/`WRITES`, which the allocator uses. | `ir/__init__.py`, `base.py`, `operands.py` |
| 3 | `tac_parser.py` | Text TAC -> IR. Infers the type of every temporary (the TAC has none) and looks up sizes in the symbol table. Fails loudly if it has to guess. | `parse_tac`, `_SymbolInfo`, `_UnitParser.operand` |
| 4 | `frames.py` | Where each value lives in memory (`home`), plus prologue/epilogue. Turns a symbol-table `address` into `-4($fp)`. | whole file (short) |
| 5 | `regalloc.py` | Register allocation (the rubric's "register selection"): `use`, `def_`, `scratch`, `into`, `flush`, `invalidate`; next-use info; spilling. | docstring, then `use`, `def_`, `_alloc` |
| 6 | `sel_core.py` | `x = y` and `x = const`. The simplest selector, a good model. | whole file |
| 7 | `sel_ops.py` | Arithmetic, comparisons, strings, `print`. Holds helpers the others share. | `sel_Binary`, `_int_arith` |
| 8 | `sel_control.py` | `if/while/for/switch` after the TAC turned them into labels and jumps. | `sel_CondJump` |
| 9 | `sel_arrays.py` | Arrays with bounds checking. | module docstring, `_element_address` |
| 10 | `sel_calls.py` | Call sequence and `return`. | module docstring |
| 11 | `sel_objects.py` | `new`, fields, virtual calls through the method table. | `sel_New`, `sel_CallVirt` |
| 12 | `sel_try.py` | `try/catch`. Flushes after every instruction when the program uses `try`. | whole file |
| 13 | `runtime.py`, `runtime_exc.py` | Routines written in MIPS appended to every program: print, alloc, string concat/equals, exception stack. | the docstring tables |
| 14 | `emitter.py` | Writes the `.s`: `.data`, `.text`, label names. | skim |
| 15 | `peephole.py` | Post-pass over the generated MIPS: 8 local rewrites. | the rule table |
| 16 | `activation.py` | Builds the frames/call tree the IDE shows. | skim |

## How a program flows through it

1. `compiler.analyze()` runs lexer, parser, semantic checks and TAC generation.
   With any error it stops and nothing below runs.
2. `generate_asm` -> `parse_tac` gives a `Program` of functions (`__main` plus
   every function and method) and classes.
3. `AsmGenerator.run()` writes `main`, then for each function:
   - `FrameInfo` (frames.py) and a fresh `RegAlloc` (regalloc.py);
   - prologue;
   - for each basic block: for each instruction `sel_<Class>` writes MIPS;
     registers are flushed before jumps and at the end of the block;
   - epilogue.
4. The runtime routines and method tables are appended.
5. `compiler.py` runs the peephole pass and returns the final `.s`.

## Where each rubric item lives

| Rubric item | Where |
|-------------|-------|
| Register selection | `regalloc.py` (+ `generator.py` flush points) |
| Activation records / tree | `frames.py`, `activation.py`; the IDE tab |
| Declarations, assignments | `sel_core.py` |
| Arithmetic, logic | `sel_ops.py` |
| Arrays | `sel_arrays.py`, `rt_new_array` |
| Control flow | `sel_control.py` (the TAC already has labels/jumps) |
| Functions, recursion | `sel_calls.py`, `frames.py` |
| Classes, inheritance | `sel_objects.py`, `emit_vtables`, layouts from the P2 |
| try/catch | `sel_try.py`, `runtime_exc.py` |
| Peephole | `peephole.py` |
| Simulator | MARS (`src/tools/Mars4_5.jar`), `src/run_mips.py` |

## Running and poking at it

```
make mips FILE=workspace/input/comp-mips/09-herencia-valido.cps    # compile + run in MARS
python3 src/run_mips.py file.cps --save out.s                      # also keep the .s
make test ARGS="src/tests/asm -q"                                  # backend tests
```

The stress programs live in `src/tests/asm/estres_casos.py`; each is
`(area, name, program, expected output)`.

## Known limits

- Nested functions that capture a variable of a function that calls itself
  recursively share one slot in `$gp` and overwrite each other.
- Integer division by zero gives an undefined value (MARS does not trap).
- The language has no `throw`; exceptions come only from out-of-range indexes
  and `null` access.
- Functions and class members must be declared before use, so mutual recursion
  cannot be written.
- Array literals of different subclasses (`[new Perro(), new Gato()]`) are
  rejected by the P1 type checker.
