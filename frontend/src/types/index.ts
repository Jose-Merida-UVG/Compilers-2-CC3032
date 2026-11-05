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
  /** Datos de memoria de semantic/layout.py; null si no aplican. */
  size: number | null;
  offset: number | null;
  /** "gp+4" (global), "fp-8" (local), "fp+8" (parámetro), "this+0" (campo). */
  address: string | null;
  /** Etiqueta de una función ("f"), método ("Clase.m") o clase. */
  label: string | null;
  /** Nombre que usa el TAC para este símbolo ("x_1" si hubo sombreado). */
  tac_name: string | null;
}

/** Registro de activación de un ámbito FUNCTION (tamaños en bytes). */
export interface FrameInfo {
  label: string;
  params_size: number;
  locals_size: number;
  temps: number;
  temps_size: number;
  saved_size: number;
  total_size: number;
}

export interface ClassField {
  name: string;
  offset: number;
  size: number;
  inherited: boolean;
}

export interface ClassMethod {
  name: string;
  label: string;
  /** Etiqueta del método del ancestro que este reemplaza, si hay. */
  overrides: string | null;
}

/** Layout de objeto de un ámbito CLASS. */
export interface ClassLayout {
  size: number;
  parent: string | null;
  fields: ClassField[];
  methods: ClassMethod[];
}

/** One node in the symbol-table scope tree, mirroring symbols.py's Scope.to_dict(). */
export interface ScopeNode {
  /** ScopeKind name: GLOBAL | FUNCTION | CLASS | BLOCK. */
  kind: string;
  /** Name of the function/class this scope belongs to, if any. */
  owner: string | null;
  symbols: SymbolEntry[];
  children: ScopeNode[];
  /** Solo en ámbitos FUNCTION. */
  frame?: FrameInfo;
  /** Solo en ámbitos CLASS. */
  layout?: ClassLayout;
}

/** Resumen del TAC generado. */
export interface TacStats {
  /** Líneas que no son func/endfunc/class/endclass. */
  instructions: number;
  /** Pico de temporales simultáneos en una función. */
  temps: number;
  /** Unidades func (métodos y __main incluidos). */
  functions: number;
}

/** Resumen del ensamblador y de la mirilla (peephole). */
export interface AsmStats {
  /** Instrucciones MIPS antes de la mirilla. */
  instructions_raw: number;
  /** Instrucciones MIPS después de la mirilla. */
  instructions: number;
  /** Transformación -> cuántas veces se aplicó. */
  peephole: Record<string, number>;
}

/** Una casilla del registro de activación (activation.frames[f].slots). */
export interface ActivationSlot {
  name: string;
  /** param | saved | local | temp. */
  kind: string;
  /** Desplazamiento respecto a $fp (positivo: hacia direcciones altas). */
  offset: number;
  /** "fp+8", "fp-4". */
  address: string;
  size: number;
}

export interface ActivationFrame {
  label: string;
  total_size: number;
  /** De direcciones altas a bajas. */
  slots: ActivationSlot[];
}

/** Nodo del árbol de activación (grafo de llamadas desplegado desde __main). */
export interface ActivationTreeNode {
  label: string;
  /** Línea TAC de la llamada que lo origina. */
  line?: string;
  recursive?: boolean;
  /** Se cortó el despliegue de la recursión en este nodo. */
  truncated?: boolean;
  /** Llamada virtual resuelta por el tipo estático. */
  virtual?: boolean;
  children: ActivationTreeNode[];
}

export interface ActivationData {
  frames: Record<string, ActivationFrame>;
  tree: ActivationTreeNode;
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
  /** Código de tres direcciones; null con cualquier error. */
  tac: string[] | null;
  tacStats: TacStats | null;
  /** Ensamblador MIPS final (con mirilla); null con errores o si el generador
   * falló, ausente si el backend aún no lo produce. */
  asm?: string[] | null;
  /** Ensamblador sin mirilla (para comparar antes/después). */
  asmRaw?: string[] | null;
  asmStats?: AsmStats | null;
  /** Marcos y árbol de activación. */
  activation?: ActivationData | null;
}

/** Lo que muestra la pestaña de ensamblador. */
export interface AsmData {
  /** Con mirilla. */
  lines: string[];
  /** Sin mirilla; null si no se conoce (p. ej. al abrir un .s guardado). */
  raw: string[] | null;
  stats: AsmStats | null;
  /** Nombre sugerido al guardar, p. ej. "prog.cps.s". */
  fileName: string;
}

/** Lo que muestra la pestaña TAC: el código o por qué no hay. */
export interface TacData {
  lines: string[] | null;
  stats: TacStats | null;
  /** Errores que impidieron generar el TAC (cuando lines es null). */
  errorCount: number;
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
  /** Tras Run (o al abrir un .tac): se muestra con el TacViewer. */
  tacData?: TacData;
  /** Tras Run (o al abrir un .s): se muestra con el AsmViewer. */
  asmData?: AsmData;
  /** Tras Run: registros y árbol de activación (ActivationViewer). */
  activationData?: ActivationData;
}

/** Error del análisis y su ubicación en el archivo fuente. */
export interface CompilerDiagnostic {
  path: string;
  message: string;
  line: number | null;
  column: number | null;
}

/** Solicitud de navegación a una posición del editor. */
export interface EditorLocation {
  path: string;
  line: number;
  column: number;
  requestId: number;
}
