# Compiscript — Lexical & Syntax Analysis

ANTLR4-based lexer and parser for Compiscript, a small C-like language. Grammar
lives in `grammar/Compiscript.g4`; ANTLR generates the lexer/parser into
`generated/`. Currently covers lexical and syntax analysis only (no semantic
analysis yet).

## Requirements

- Java (JRE 11+) — only needed to run the ANTLR tool jar for code generation
- Python 3.8+
- `antlr4-python3-runtime` (must match the ANTLR jar version)

## Install

```
pip install -r requirements.txt
```

The ANTLR tool jar is already vendored at `tools/antlr-4.13.2-complete.jar`
(used only for regenerating the parser, not at runtime).

## Generating the parser

Run this after any change to `grammar/Compiscript.g4`:

```
./generate.sh
```

This regenerates `CompiscriptLexer.py`, `CompiscriptParser.py`,
`CompiscriptVisitor.py`, and `CompiscriptListener.py` into `generated/`.

## Running

```
PYTHONPATH=generated:src python3 src/main.py <path-to-source-file>
```

This lexes and parses the file, prints any lexical/syntax errors, then prints
the resulting parse tree.

## Running the tests

Two sample programs live in `tests/`:

- `tests/valid.cps` — a well-formed program, should parse cleanly with no errors
- `tests/invalid.cps` — contains a lexical error (illegal character) and two
  syntax errors, to exercise error reporting

```
PYTHONPATH=generated:src python3 src/main.py tests/valid.cps
PYTHONPATH=generated:src python3 src/main.py tests/invalid.cps
```
