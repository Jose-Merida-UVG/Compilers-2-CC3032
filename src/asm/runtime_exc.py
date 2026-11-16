"""Excepciones en MIPS.

Cada `try` apila `[catch][$sp][$fp]` en `exc_stack`; `rt_throw` restaura `$sp` y
`$fp` del manejador de arriba y salta a su catch. Sin manejador, imprime el
mensaje y termina.

    rt_try_push    $a0 = dirección del catch
    rt_try_pop
    rt_throw       $a0 = mensaje
    rt_throw_index índice fuera de rango o tamaño negativo
    rt_throw_null  campo o método de `null`
"""

from __future__ import annotations

from asm.emitter import AsmEmitter

HANDLER_SIZE = 12  # [catch][$sp][$fp]
MAX_HANDLERS = 256  # `try` anidados (o recursivos) a la vez


def emit_exc_runtime(asm: AsmEmitter) -> None:
    """Escribe en `.data` la pila de manejadores y los mensajes, y en `.text` las rutinas de excepciones."""
    ins, label = asm.ins, asm.label

    asm.data("        .align 2")
    asm.data("exc_msg: .word 0")  # Mensaje de la última excepción
    asm.data("exc_top: .word exc_stack")  # Primer lugar libre de la pila
    asm.data(f"exc_stack: .space {HANDLER_SIZE * MAX_HANDLERS}")
    asm.data('rt_msg_uncaught: .asciiz "Excepcion no capturada: "')
    asm.data('rt_msg_index: .asciiz "indice fuera de rango"')
    asm.data('rt_msg_null: .asciiz "referencia nula"')

    asm.comment("──────── excepciones ────────")
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
    ins("beq   $v0, $v1, rt_throw_uncaught")  # No hay manejador
    ins(f"addiu $v0, $v0, -{HANDLER_SIZE}")
    ins("sw    $v0, exc_top")
    ins("lw    $a1, 0($v0)")
    ins("lw    $sp, 4($v0)")
    ins("lw    $fp, 8($v0)")
    ins("jr    $a1")  # A la etiqueta del `catch`, en el marco del `try`

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
