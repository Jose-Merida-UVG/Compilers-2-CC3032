"""Runtime del Proyecto 3: impresión, memoria y strings (parte de Nes).

Contrato: docs/proyecto3/01-contrato.md §7. Cada rutina se llama con `jal` y
**preserva todos los registros salvo** `$v0,$v1,$a0-$a3,$f0,$f12,$at`; las que
necesitan más registros usan solo esos (guardan `$ra` y lo demás en la pila).
Por eso un selector puede llamarlas a mitad de un bloque sin `flush()`.

    rt_print_int     $a0                imprime el entero + "\n"
    rt_print_float   $f12               imprime el float + "\n"
    rt_print_bool    $a0 (0/1)          imprime true/false + "\n"
    rt_print_str     $a0 (puntero)      imprime el string + "\n"
    rt_alloc         $a0 = bytes        $v0 = memoria en cero (múltiplo de 4)
    rt_new_array     $a0 = n            $v0 = [n][0 ... 0]; n < 0 lanza
    rt_str_concat    $a0, $a1           $v0 = string nuevo
    rt_str_eq        $a0, $a1           $v0 = 1 si el contenido es igual, si no 0

`print` siempre agrega el salto de línea. Las rutinas de excepciones
(`rt_throw_index`, `rt_throw`, ...) son de Tono (`runtime_exc.py`); mientras
ese archivo no exista se emite un `rt_throw_index` mínimo para que el `.s`
ensamble.
"""

from __future__ import annotations

import importlib.util

from asm.emitter import AsmEmitter


def emit_runtime(asm: AsmEmitter) -> None:
    ins, label = asm.ins, asm.label

    asm.data('rt_true:  .asciiz "true\\n"')
    asm.data('rt_false: .asciiz "false\\n"')

    def newline() -> None:
        ins("li    $v0, 11")
        ins("li    $a0, 10")
        ins("syscall")

    asm.comment("──────── runtime (Nes) ────────")

    # -- impresión ---------------------------------------------------------
    label("rt_print_int")
    ins("li    $v0, 1")
    ins("syscall")
    newline()
    ins("jr    $ra")

    label("rt_print_float")
    ins("li    $v0, 2")  # imprime $f12
    ins("syscall")
    newline()
    ins("jr    $ra")

    label("rt_print_bool")
    ins("beq   $a0, $zero, rt_print_bool_f")
    ins("la    $a0, rt_true")
    ins("j     rt_print_bool_go")
    label("rt_print_bool_f")
    ins("la    $a0, rt_false")
    label("rt_print_bool_go")
    ins("li    $v0, 4")  # el mensaje ya termina en "\n"
    ins("syscall")
    ins("jr    $ra")

    label("rt_print_str")
    ins("li    $v0, 4")
    ins("syscall")
    newline()
    ins("jr    $ra")

    # -- memoria ---------------------------------------------------------------
    label("rt_alloc")  # $a0 = bytes -> $v0 (sbrk entrega memoria en cero)
    ins("addiu $a0, $a0, 3")
    ins("srl   $a0, $a0, 2")
    ins("sll   $a0, $a0, 2")  # redondeo a múltiplo de 4
    ins("li    $v0, 9")
    ins("syscall")
    ins("jr    $ra")

    label("rt_new_array")  # $a0 = n -> $v0 = [n][e0 .. e(n-1)] en cero
    ins("bltz  $a0, rt_throw_index")
    ins("addiu $sp, $sp, -8")
    ins("sw    $ra, 4($sp)")
    ins("sw    $a0, 0($sp)")
    ins("sll   $a0, $a0, 2")
    ins("addiu $a0, $a0, 4")  # 4 de cabecera + 4 por elemento
    ins("jal   rt_alloc")
    ins("lw    $a0, 0($sp)")
    ins("sw    $a0, 0($v0)")  # longitud
    ins("lw    $ra, 4($sp)")
    ins("addiu $sp, $sp, 8")
    ins("jr    $ra")

    # -- strings ---------------------------------------------------------------
    label("rt_str_concat")  # $a0 + $a1 -> $v0
    ins("addiu $sp, $sp, -16")
    ins("sw    $ra, 12($sp)")
    ins("sw    $a0, 8($sp)")
    ins("sw    $a1, 4($sp)")
    ins("move  $v1, $a0")  # longitud de $a0
    label("rt_cat_l0")
    ins("lb    $a2, 0($v1)")
    ins("beq   $a2, $zero, rt_cat_l0_end")
    ins("addiu $v1, $v1, 1")
    ins("j     rt_cat_l0")
    label("rt_cat_l0_end")
    ins("subu  $v1, $v1, $a0")
    ins("move  $a2, $a1")  # longitud de $a1
    label("rt_cat_l1")
    ins("lb    $a3, 0($a2)")
    ins("beq   $a3, $zero, rt_cat_l1_end")
    ins("addiu $a2, $a2, 1")
    ins("j     rt_cat_l1")
    label("rt_cat_l1_end")
    ins("subu  $a2, $a2, $a1")
    ins("addu  $a0, $v1, $a2")
    ins("addiu $a0, $a0, 1")  # + terminador '\0'
    ins("jal   rt_alloc")  # solo toca $a0 y $v0
    ins("lw    $a0, 8($sp)")
    ins("lw    $a1, 4($sp)")
    ins("move  $v1, $v0")  # puntero de escritura
    label("rt_cat_c0")
    ins("lb    $a2, 0($a0)")
    ins("beq   $a2, $zero, rt_cat_c1")
    ins("sb    $a2, 0($v1)")
    ins("addiu $a0, $a0, 1")
    ins("addiu $v1, $v1, 1")
    ins("j     rt_cat_c0")
    label("rt_cat_c1")
    ins("lb    $a2, 0($a1)")  # copia $a1 incluido el '\0'
    ins("sb    $a2, 0($v1)")
    ins("beq   $a2, $zero, rt_cat_done")
    ins("addiu $a1, $a1, 1")
    ins("addiu $v1, $v1, 1")
    ins("j     rt_cat_c1")
    label("rt_cat_done")
    ins("lw    $ra, 12($sp)")
    ins("addiu $sp, $sp, 16")
    ins("jr    $ra")

    label("rt_str_eq")  # $a0 == $a1 (por contenido) -> $v0 = 1/0
    label("rt_eq_loop")
    ins("lb    $v1, 0($a0)")
    ins("lb    $a2, 0($a1)")
    ins("bne   $v1, $a2, rt_eq_no")
    ins("beq   $v1, $zero, rt_eq_yes")  # ambos terminaron a la vez
    ins("addiu $a0, $a0, 1")
    ins("addiu $a1, $a1, 1")
    ins("j     rt_eq_loop")
    label("rt_eq_yes")
    ins("li    $v0, 1")
    ins("jr    $ra")
    label("rt_eq_no")
    ins("li    $v0, 0")
    ins("jr    $ra")

    # -- respaldo mientras Tono no entregue runtime_exc.py ------------------------
    if importlib.util.find_spec("asm.runtime_exc") is None:
        asm.data('rt_msg_index: .asciiz "Excepcion no capturada: indice fuera de rango\\n"')
        asm.comment("rt_throw_index provisional (se reemplaza por el de runtime_exc.py)")
        label("rt_throw_index")
        ins("la    $a0, rt_msg_index")
        ins("li    $v0, 4")
        ins("syscall")
        ins("li    $a0, 1")
        ins("li    $v0, 17")
        ins("syscall")
