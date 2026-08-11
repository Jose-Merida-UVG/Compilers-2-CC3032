# Compiscript — Lexical & Syntax Analysis

ANTLR4-based lexer and parser for Compiscript, a small C-like language.
Everything compiler-related (grammar, generated parser, CLI, server, tests)
lives under `src/`; `frontend/` is the browser IDE UI. Currently covers
lexical and syntax analysis only (no semantic analysis yet).

## Requirements

- Java (JRE 11+) — only needed to run the ANTLR tool jar for code generation
- Python 3.8+
- `antlr4-python3-runtime` (must match the ANTLR jar version)

## Install

```
make install
```

This creates a `.venv` (if one doesn't already exist) and installs
dependencies into it. Every other Python-facing target (`run`, `backend`,
`test`) automatically uses `.venv` when present, falling back to the system
`python3`/`pip` otherwise.

The ANTLR tool jar is already vendored at `src/tools/antlr-4.13.2-complete.jar`
(used only for regenerating the parser, not at runtime).

## Generating the parser

Run this after any change to `src/grammar/Compiscript.g4`:

```
make generate
```

This regenerates `CompiscriptLexer.py`, `CompiscriptParser.py`,
`CompiscriptVisitor.py`, and `CompiscriptListener.py` into `src/generated/`.

## Running

```
make run FILE=<path-to-source-file>
```

This lexes and parses the file, prints any lexical/syntax errors, then prints
the resulting parse tree.

## Running the tests

Sample programs live in `src/tests/`, covering valid input plus lexical,
syntax, and mixed errors.

```
make test
```

Or run one directly:

```
make run FILE=src/tests/valid.cps
```

## Web IDE (frontend + backend)

There's also a browser-based IDE in `frontend/` (React + Monaco) backed by a
small FastAPI server in `src/server.py`. It edits files under `workspace/`
(seeded with sample `.cps` programs) and runs them through the same
lex/parse pipeline as the CLI (`src/compiler.py`, shared by both).

Backend:

```
make backend
```

Frontend (in another terminal):

```
make frontend-install   # first time only
make frontend-dev
```

Open the printed Vite URL (default `http://localhost:5173`). It proxies
`/api/*` to the backend on port 8080 (see `frontend/vite.config.ts`). Open a
`.cps` file in the explorer and click **▶ Run** to see lexical/syntax errors
and the parse tree, both as text in the output panel and as a collapsible
tree viewer.
