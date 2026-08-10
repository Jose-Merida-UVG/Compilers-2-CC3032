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

## Web IDE (frontend + backend)

There's also a browser-based IDE in `frontend/` (React + Monaco) backed by a
small FastAPI server in `src/server.py`. It edits files under `workspace/`
(seeded with copies of the two test programs) and runs them through the same
lex/parse pipeline as the CLI (`src/compiler.py`, shared by both).

Backend:

```
pip install -r requirements.txt
PYTHONPATH=generated:src uvicorn server:app --app-dir src --reload --port 8080
```

Frontend (in another terminal):

```
cd frontend
npm install
npm run dev
```

Open the printed Vite URL (default `http://localhost:5173`). It proxies
`/api/*` to the backend on port 8080 (see `frontend/vite.config.ts`). Open a
`.cps` file in the explorer and click **▶ Run** to see lexical/syntax errors
and the parse tree, both as text in the output panel and as a collapsible
tree viewer.
