# Proyecto 3: código objeto (MIPS)

Traduce el TAC (texto) y la tabla de símbolos del P2 a ensamblador MIPS32 para
MARS/SPIM. Vive en `src/asm/`; la entrada es `generate_asm(tac, symbol_table)`
(`generator.py`) y la llama `compiler.analyze()` solo si no hubo ningún error.
Si el generador falla, el error se reporta como "Error interno al generar el
ensamblador" y no se publica ni TAC ni MIPS.

## 1. Flujo

```
TAC (texto) + tabla de símbolos (JSON)
   │  tac_parser.parse_tac         texto → objetos del IR (Program)
   ▼
   │  por cada función:
   │    split_blocks + block_live_out    bloques básicos y temporales vivos
   │    por cada instrucción:  generator._dispatch  →  sel_<Clase>(ins)
   ▼                                   │ el selector pide registros a RegAlloc
MIPS crudo + datos de activación       ▼ y escribe con AsmEmitter
   │  peephole.optimize (opcional)
   ▼
MIPS final
```

## 2. Orden de dependencias (de abajo hacia arriba)

Cada nivel solo importa de los anteriores.

| Nivel | Archivo | Rol |
|---|---|---|
| 0 | `ir/` | El vocabulario: tipos, operandos e instrucciones como objetos (§3). |
| 0 | `emitter.py` | Acumula `.text` y `.data`: `ins`, `label`, `string`, `float_`, `new_label`; nombres seguros (`f_Animal__hablar`, `vt_Animal`). |
| 1 | `tac_parser.py` | TAC texto → `Program` del IR; resuelve tipos, offsets de campos y tamaños con la tabla de símbolos. |
| 1 | `frames.py` | Dónde vive cada valor (`home`) y el prólogo/epílogo de cada función. |
| 1 | `regalloc.py` | `getReg`: qué valor ocupa qué registro en cada momento (§5). |
| 2 | `sel_*.py` | Selectores: un método por clase de instrucción (§6). |
| 2 | `runtime.py` | Rutinas en MIPS: `print`, `rt_alloc`, arreglos, strings. |
| 3 | `generator.py` | El driver: recorre el IR y despacha a los selectores. |

## 3. El IR (`ir/`)

Cada línea del TAC es un objeto. Tres capas:

- **`Ty`** (`types.py`): tipo estático de un valor. Elige la instrucción MIPS:
  `addu` / `add.s` / `rt_str_concat`, `lw` / `lwc1` / `lb`.

  | `kind` | Valor | En memoria |
  |---|---|---|
  | `int`, `bool`, `float` | escalares | palabra (el `bool` ocupa 1 byte en su casa; el `float` va en registros `$f`) |
  | `str` | string | puntero a `.asciiz` |
  | `array` (`elem`) | arreglo | puntero a `[longitud][e0][e1]…` |
  | `obj` (`cls`) | instancia | puntero a `[tabla de métodos][campo0]…` |
  | `vtable` | tabla de métodos de un objeto | puntero a la lista de métodos |
  | `null`, `void`, `unknown` | marcadores | `null` es 0 |

- **`Operand`** (`operands.py`): un valor concreto del TAC. Tiene `text` (tal
  cual en el TAC; también es su identidad en el asignador, `key`), `kind`
  (`var` con casa en memoria, `temp` que muere tras su último uso, `const` sin
  casa), `ty`, y `value` solo para constantes (`None` en var/temp; `null` también
  es `None`, así que se revisa `is_const` primero).
- **`Instr`** (`base.py` y los demás módulos): una clase por instrucción del TAC,
  con operandos como campos. Cada una expone `reads()` y `writes()`, que el
  asignador usa para calcular el siguiente uso; `_vals` descarta constantes y
  `None`. `line` guarda el TAC original, que se emite como comentario.

Ejemplo: `$t1 = b * 2` →
`Binary(dst=$t1:temp:int, a=b:var:int, op="*", b=2:const:int, line="$t1 = b * 2")`.

No toda línea es una instrucción: los `param` se pliegan en el `Call` que
sigue, y `func`/`class`/`vtable` forman las unidades `FuncUnit`, `ClassUnit` y
`Program` (`units.py`).

| Módulo | Contenido |
|---|---|
| `types.py` | `Ty`, `INT`, `FLOAT`, …, `array_of`, `obj_of` |
| `operands.py` | `Operand` |
| `base.py` | `Instr`, `_vals` |
| `control.py` | `Label`, `Goto`, `CondJump`, `Return`, `TERMINATORS` |
| `values.py` | `Copy`, `Unary`, `Binary`, `Print` |
| `arrays.py` | `NewArray`, `Len`, `IndexLoad`, `IndexStore` |
| `objects.py` | `FieldLoad`, `FieldStore`, `New`, `VTableLoad` |
| `calls.py` | `Call`, `CallVirt` |
| `exceptions.py` | `Try`, `EndTry`, `Catch` |
| `units.py` | `FuncUnit`, `ClassUnit`, `Program` |

`ir/__init__.py` reexporta todo, así que se importa siempre `from asm.ir import …`.

## 4. Modelo de memoria

Registro de activación (`frames.py`); la pila crece hacia abajo:

```
fp+8+4*i   argumento i (i = 0 es `this` en un método)
fp+4       $ra guardado
fp+0       $fp del llamador            <- $fp apunta aquí
fp-4 …     locales
debajo     temporales $t1, $t2, … (4 bytes cada uno)
```

- Toda variable y temporal tiene una **casa** fija en memoria, `N($fp)` o
  `N($gp)` (globales); sale de las direcciones que calcula `semantic/layout.py`.
  Nada se direcciona relativo a `$sp`, así que empujar argumentos no invalida
  casas.
- **Llamada**: `addiu $sp,-4n`, `sw` de cada argumento a `4*i($sp)`, `flush`,
  `jal`, `invalidate`, se libera la pila. Retorno en `$v0` (o `$f0` si es float).
- **Heap**: `rt_alloc` (`$a0` = bytes, devuelve `$v0`, memoria en cero).
  Arreglo: `[n][e0]…` con 4 bytes por elemento; la lectura verifica rango y
  salta a `rt_throw_index`.
- **Objeto**: `[tabla de métodos][campos]`; los campos empiezan en el offset 4.
  **Tabla de métodos** (`vt_<Clase>` en `.data`): una palabra por slot con la
  dirección del método; un método sobrescrito reutiliza el slot del padre. Una
  llamada a método es `x = vtable obj` (lee la palabra 0), `$t = $t[slot]`
  (lee el slot, sin cabecera ni verificación de rango) y `callvirt`.

## 5. Asignador de registros (`regalloc.py`)

El algoritmo de Aho §8.6.3: un descriptor de registros (qué valor tiene cada
uno), uno de direcciones (dónde está cada valor) y el **siguiente uso**
calculado hacia atrás en cada bloque. Un temporal sin siguiente uso está muerto:
libera su registro y no se guarda; las variables nunca mueren. Pool: `$t0-$t9` y
`$f4, $f6, $f8, $f10, $f14, $f16, $f18` (`$f12` queda reservado). Política *caller-saved*: todo lo sucio y vivo se guarda a su
casa antes de cada salto y de cada `jal`; después de una etiqueta o llamada no se
confía en ningún registro. Los registros ABI `$a0-$a3`, `$v0`, `$v1`, `$f0`,
`$f12` y `$at` nunca se entregan: los selectores los usan a mano.

| Método | Qué hace |
|---|---|
| `use(op)` | Registro con el valor de `op`; lo carga de su casa si hace falta. |
| `def_(op)` | Registro para un resultado; puede reutilizar el de un fuente ya muerto. |
| `scratch()` | Registro anónimo hasta el fin de la instrucción. |
| `into(reg, op)` | Deja `op` en un registro fijo (`$a0`, `$f12`, …). |
| `flush()` | Guarda a su casa lo sucio y vivo. |
| `invalidate()` | Olvida todos los registros (tras `jal`). |

Reglas: pedir los fuentes con `use` antes del destino con `def_` (puede devolver
el mismo registro que un fuente muerto; `avoid=` lo evita); no nombrar registros
para valores; las rutinas del runtime solo tocan registros reservados, así que
se pueden llamar a mitad de una instrucción sin `flush`. Cada decisión queda en
`regs.trace`.

## 6. Selectores (`sel_*.py`)

Un *selector* decide qué instrucciones MIPS emitir para una instrucción del TAC.
El driver busca el método `sel_<NombreDeClase>` (`sel_Binary`, `sel_Call`, …) y
lo llama con el objeto del IR. Un selector típico (`sel_Copy`):

```python
rs = regs.use(src)
rd = regs.def_(dst)
if rd != rs: asm.ins(f"move  {rd}, {rs}")
```

Los selectores son *mixins*: `AsmGenerator` los junta. Si falta un `sel_X`, el
driver falla con `falta el selector sel_X`. El driver antepone un `flush` a
`Return`, `Goto` y `CondJump`, y vacía los registros al entrar a cada bloque.

| Archivo | Instrucciones |
|---|---|
| `sel_core.py` | `Copy` |
| `sel_ops.py` | `Unary`, `Binary`, `Print` (enteros, floats, strings) |
| `sel_control.py` | `Goto`, `CondJump` |
| `sel_arrays.py` | `NewArray`, `Len`, `IndexLoad`, `IndexStore` |
| `sel_calls.py` | `Call`, `Return` |
| `sel_objects.py` | `New`, `FieldLoad`, `FieldStore`, `VTableLoad`, `CallVirt`, y `emit_vtables` *(pendiente)* |
| `sel_try.py` | `Try`, `EndTry`, `Catch` *(pendiente)* |
| `runtime_exc.py` | pila de manejadores, `rt_throw_index`, `rt_throw` *(pendiente)* |
| `peephole.py` | `optimize(lines)`: mirilla sobre el MIPS *(pendiente, opcional)* |
| `activation.py` | `build_activation(program, frames)`: datos del IDE *(pendiente, opcional)* |

El driver importa con respaldo los módulos que faltan (clase vacía), así que el
resto compila; un programa que use una instrucción sin selector falla con el
mensaje de arriba.

## 7. Pruebas

`src/tests/asm/<categoría>/`: casos `.cps` con su salida esperada `.out`, un
simulador mínimo (`support/minisim.py`) y pruebas del parser, de los marcos y de
`getReg` (`registros/`). `make test` los corre junto al resto.
