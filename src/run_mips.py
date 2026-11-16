"""Compila un `.cps` a MIPS y lo ejecuta en MARS.

    python3 src/run_mips.py archivo.cps [--save salida.s]

Imprime lo que imprime el programa. Con errores no ejecuta nada. Usa `java` y el
jar de MARS: `MARS_JAR` o `src/tools/Mars4_5.jar`.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

from compiler import analyze_file

HERE = os.path.dirname(os.path.abspath(__file__))


def find_mars() -> str | None:
    for candidate in (os.environ.get("MARS_JAR", ""), os.path.join(HERE, "tools", "Mars4_5.jar")):
        if candidate and os.path.isfile(candidate):
            return candidate
    return None


MAX_OUTPUT = 100_000  # caracteres de salida que se devuelven
TIMEOUT = 10.0  # segundos antes de matar un programa que no termina


def _text(data) -> str:
    if data is None:
        return ""
    return data.decode("utf-8", "replace") if isinstance(data, bytes) else data


def execute(asm: list[str], timeout: float = TIMEOUT) -> dict:
    """Ejecuta el ensamblador en MARS.

    Devuelve `{available, output, stderr, exitCode, timedOut}`. `available` es
    False si falta `java` o el jar (no se ejecutó nada); `exitCode` es None si se
    cortó por tiempo."""
    jar = find_mars()
    if jar is None or shutil.which("java") is None:
        return {"available": False, "output": "", "stderr": "", "exitCode": None, "timedOut": False}

    with tempfile.NamedTemporaryFile("w", suffix=".s", delete=False, encoding="utf-8") as fh:
        fh.write("\n".join(asm) + "\n")
    try:
        proc = subprocess.run(
            ["java", "-Djava.awt.headless=true", "-jar", jar, "nc", "sm", fh.name],
            capture_output=True, text=True, encoding="utf-8", timeout=timeout,
        )
        out, err, code, timed_out = proc.stdout, proc.stderr, proc.returncode, False
        if out.endswith("\n\n") or out == "\n":  # MARS agrega un "\n" al terminar
            out = out[:-1]
    except subprocess.TimeoutExpired as exc:
        out, err, code, timed_out = _text(exc.stdout), _text(exc.stderr), None, True
    finally:
        os.unlink(fh.name)

    if len(out) > MAX_OUTPUT:
        out = out[:MAX_OUTPUT] + "\n… (salida truncada)\n"
    return {"available": True, "output": out, "stderr": err, "exitCode": code, "timedOut": timed_out}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Compila un .cps a MIPS y lo ejecuta en MARS")
    parser.add_argument("file")
    parser.add_argument("--save", metavar="SALIDA.s", help="además guarda el ensamblador")
    args = parser.parse_args(argv)

    result = analyze_file(args.file)
    if result["asm"] is None:
        for err in result["errors"]:
            print(err)
        print(result["status_message"])
        return 1

    if args.save:
        with open(args.save, "w", encoding="utf-8") as fh:
            fh.write("\n".join(result["asm"]) + "\n")

    run = execute(result["asm"])
    if not run["available"]:
        print("Falta java o Mars4_5.jar (MARS_JAR o src/tools/Mars4_5.jar).", file=sys.stderr)
        return 2
    sys.stdout.write(run["output"])
    sys.stderr.write(run["stderr"])
    if run["timedOut"]:
        print(f"\nSe cortó la ejecución: pasó de {TIMEOUT:g} s.", file=sys.stderr)
        return 3
    return run["exitCode"]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
