import sys

from compiler import analyze_file

USAGE = "usage: python3 main.py [--asm] <path-to-source-file>"


# CLI interface
def main() -> None:
    args = sys.argv[1:]
    show_asm = "--asm" in args
    paths = [a for a in args if a != "--asm"]
    if len(paths) != 1:
        print(USAGE, file=sys.stderr)
        sys.exit(1)

    result = analyze_file(paths[0])

    for err in result["errors"]:
        print(err)

    print(result["status_message"])

    # Con cualquier error (incluido uno interno del generador) no hay TAC ni
    # ensamblador (R9): ambos vienen en None.
    if show_asm:
        if result["asm"] is not None:
            print()
            print("\n".join(result["asm"]))
    elif result["tac"] is not None:
        print()
        print("\n".join(result["tac"]))


if __name__ == "__main__":
    main()
