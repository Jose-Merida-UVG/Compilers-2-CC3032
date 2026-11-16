"""TAC del Proyecto 2 -> MIPS para MARS. La guía completa está en `map.md`.

Términos: IR (el TAC como objetos, en `ir/`), selector (método `sel_<Clase>`
que traduce una instrucción del IR), casa (dirección en memoria de una
variable o temporal), flush (guardar los registros sucios a su casa).

Orden de lectura:

  generator.py    `generate_asm` (al final) y el recorrido de funciones
  ir/             las clases del IR
  tac_parser.py   texto TAC -> IR, con tipos
  frames.py       casas en memoria, prólogo y epílogo
  regalloc.py     asignador de registros
  sel_*.py        selectores: core, ops, control, arrays, calls, objects, try
  runtime*.py     rutinas en MIPS (print, memoria, strings, excepciones)
  emitter.py      escritura del `.s`
  peephole.py     optimización del MIPS generado
  activation.py   datos de marcos y árbol de llamadas para el IDE

Resumen con ejemplo trazado: README, sección "Código objeto (MIPS)".
"""
