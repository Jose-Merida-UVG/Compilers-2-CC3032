// Mirror of the dicts returned by src/server.py (FastAPI backend).

export interface FileNode {
  name: string;
  path: string;
  isDir: boolean;
  children?: FileNode[];
}

/** A node in the ANTLR parse tree, serialized for the frontend's tree viewer. */
export interface ParseTreeNode {
  label: string;
  isTerminal: boolean;
  children: ParseTreeNode[];
}

/** One symbol declared in a Scope, mirroring semantic/symbols.py's Symbol. */
export interface SymbolEntry {
  name: string;
  /** SymbolKind name: VARIABLE | CONSTANT | PARAMETER | FUNCTION | CLASS. */
  kind: string;
  /** str(Type) from the semantic checker, e.g. "integer", "integer[]", "(integer) -> string". */
  type: string;
  line: number;
  column: number;
}

/** One node in the symbol-table scope tree, mirroring symbols.py's Scope.to_dict(). */
export interface ScopeNode {
  /** ScopeKind name: GLOBAL | FUNCTION | CLASS | BLOCK. */
  kind: string;
  /** Name of the function/class this scope belongs to, if any. */
  owner: string | null;
  symbols: SymbolEntry[];
  children: ScopeNode[];
}

export interface RunOutput {
  /** Terminal-ready lines: errors, then the status message. */
  lines: string[];
  /** Lexical/syntax error messages only. */
  errors: string[];
  /** Spanish summary: success text if no errors, otherwise an error count. */
  statusMessage: string;
  /** The parse tree as a nested structure, for the ParseTreeViewer. */
  tree: ParseTreeNode | null;
  /** The scope tree, for the SymbolTableViewer -- null if semantic
   * analysis didn't run (lexical/syntax errors present). */
  symbolTable: ScopeNode | null;
}

export interface EditorTab {
  path: string;
  label: string;
  content: string;
  isDirty: boolean;
  /** Populated after Run — renders the ParseTreeViewer instead of Monaco. */
  treeData?: ParseTreeNode;
  /** Populated after Run — renders the SymbolTableViewer instead of Monaco. */
  symbolTableData?: ScopeNode;
}
