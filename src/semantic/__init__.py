"""Semantic analysis for Compiscript: type system, symbol table, and the
tree-walking checker that applies the semantic rules from
docs/plan-proyecto1.md.

Layout:
  types.py    - the Type hierarchy (Integer, Float, Array, Function, ...)
  symbols.py  - Symbol / Scope / SymbolTable
  errors.py   - SemanticError / SemanticErrorList (same shape as
                error_listener.py's list, kept separate on purpose --
                lexical/syntax errors come from ANTLR, semantic errors
                come from walking the already-built tree)
  checker.py  - SemanticChecker(CompiscriptVisitor), the actual rules
"""
