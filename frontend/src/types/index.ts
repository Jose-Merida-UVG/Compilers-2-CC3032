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

export interface RunOutput {
  /** Terminal-ready lines: errors, then the status message. */
  lines: string[];
  /** Lexical/syntax error messages only. */
  errors: string[];
  /** Spanish summary: success text if no errors, otherwise an error count. */
  statusMessage: string;
  /** The parse tree as a nested structure, for the ParseTreeViewer. */
  tree: ParseTreeNode | null;
}

export interface EditorTab {
  path: string;
  label: string;
  content: string;
  isDirty: boolean;
  /** Populated after Run — renders the ParseTreeViewer instead of Monaco. */
  treeData?: ParseTreeNode;
}
