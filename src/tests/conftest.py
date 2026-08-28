"""Makes `import compiler`, `from semantic...`, etc. work from any test
file under src/tests/, regardless of how pytest is invoked (IDE, `make
test`, bare `pytest`) -- mirrors the PYTHONPATH=src/generated:src that the
Makefile/README already use for the CLI and server.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.dirname(_HERE)
_GENERATED = os.path.join(_SRC, "generated")

for path in (_GENERATED, _SRC):
    if path not in sys.path:
        sys.path.insert(0, path)
