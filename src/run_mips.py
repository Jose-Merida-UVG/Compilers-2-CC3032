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

    jar = find_mars()
    if jar is None or shutil.which("java") is None:
        print("Falta java o Mars4_5.jar (MARS_JAR o src/tools/Mars4_5.jar).", file=sys.stderr)
        return 2

    source = "\n".join(result["asm"]) + "\n"
    if args.save:
        with open(args.save, "w", encoding="utf-8") as fh:
            fh.write(source)
    with tempfile.NamedTemporaryFile("w", suffix=".s", delete=False, encoding="utf-8") as fh:
        fh.write(source)
    try:
        proc = subprocess.run(
            ["java", "-Djava.awt.headless=true", "-jar", jar, "nc", "sm", fh.name],
            capture_output=True, text=True, encoding="utf-8",
        )
    finally:
        os.unlink(fh.name)

    out = proc.stdout
    if out.endswith("\n\n") or out == "\n":  # MARS agrega un "\n" al terminar
        out = out[:-1]
    sys.stdout.write(out)
    sys.stderr.write(proc.stderr)
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
