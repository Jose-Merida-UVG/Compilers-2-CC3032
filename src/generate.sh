#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
java -jar tools/antlr-4.13.2-complete.jar -Dlanguage=Python3 -visitor -o generated grammar/Compiscript.g4

# ANTLR mirrors the grammar file's directory under -o; flatten it back out.
if [ -d generated/grammar ]; then
  mv generated/grammar/* generated/
  rmdir generated/grammar
fi
