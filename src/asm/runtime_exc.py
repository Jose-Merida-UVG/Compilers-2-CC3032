"""Excepciones en tiempo de ejecución (Tono).

Pila de manejadores en `.data`: cada `try` apila `[dirección del catch][$sp][$fp]`
y `endtry` la desapila. `rt_throw` restaura `$sp` y `$fp` del manejador de arriba
y salta a su catch; si no hay ninguno, imprime el mensaje y termina. Los
registros ya están guardados en sus casas antes de cada llamada (política
*caller-saved*), así que desenrollar no restaura nada más.

    rt_try_push    $a0 = dirección del catch
    rt_try_pop
    rt_throw       $a0 = mensaje (string)
    rt_throw_index índice fuera de rango o tamaño de arreglo negativo
    rt_throw_null  acceso a un campo o método de `null`

Solo tocan `$v0`, `$v1`, `$a0`, `$a1` y `$at`.
"""

from __future__ import annotations

from asm.emitter import AsmEmitter

HANDLER_SIZE = 12  # [catch][$sp][$fp]
MAX_HANDLERS = 256  # `try` anidados (o recursivos) a la vez


def emit_exc_runtime(asm: AsmEmitter) -> None:
    ins, label = asm.ins, asm.label

    asm.data("        .align 2")
    asm.data("exc_msg: .word 0")  # mensaje de la última excepción
    asm.data("exc_top: .word exc_stack")  # primer lugar libre de la pila
    asm.data(f"exc_stack: .space {HANDLER_SIZE * MAX_HANDLERS}")
    asm.data('rt_msg_uncaught: .asciiz "Excepcion no capturada: "')
    asm.data('rt_msg_index: .asciiz "indice fuera de rango"')
    asm.data('rt_msg_null: .asciiz "referencia nula"')

    asm.comment("──────── excepciones (Tono) ────────")
    label("rt_try_push")  # $a0 = catch
    ins("lw    $v0, exc_top")
    ins("sw    $a0, 0($v0)")
    ins("sw    $sp, 4($v0)")
    ins("sw    $fp, 8($v0)")
    ins(f"addiu $v0, $v0, {HANDLER_SIZE}")
    ins("sw    $v0, exc_top")
    ins("jr    $ra")

    label("rt_try_pop")
    ins("lw    $v0, exc_top")
    ins(f"addiu $v0, $v0, -{HANDLER_SIZE}")
    ins("sw    $v0, exc_top")
    ins("jr    $ra")

    label("rt_throw_index")
    ins("la    $a0, rt_msg_index")
    ins("j     rt_throw")

    label("rt_throw_null")
    ins("la    $a0, rt_msg_null")

    label("rt_throw")  # $a0 = mensaje
    ins("sw    $a0, exc_msg")
    ins("lw    $v0, exc_top")
    ins("la    $v1, exc_stack")
    ins("beq   $v0, $v1, rt_throw_uncaught")  # no hay manejador
    ins(f"addiu $v0, $v0, -{HANDLER_SIZE}")
    ins("sw    $v0, exc_top")
    ins("lw    $a1, 0($v0)")
    ins("lw    $sp, 4($v0)")
    ins("lw    $fp, 8($v0)")
    ins("jr    $a1")  # a la etiqueta del `catch`, en el marco del `try`

    label("rt_throw_uncaught")
    ins("la    $a0, rt_msg_uncaught")
    ins("li    $v0, 4")
    ins("syscall")
    ins("lw    $a0, exc_msg")
    ins("li    $v0, 4")
    ins("syscall")
    ins("li    $a0, 10")
    ins("li    $v0, 11")
    ins("syscall")
    ins("li    $a0, 1")
    ins("li    $v0, 17")
    ins("syscall")
