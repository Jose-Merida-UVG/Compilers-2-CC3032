// Mirror of Go structs returned by the Wails backend.

export interface FileNode {
  name: string;
  path: string;
  isDir: boolean;
  children?: FileNode[];
}

export interface LetDefinitionDTO {
  identifier: string;
  regex: string;
}

export interface PatternDTO {
  pattern: string;
  action: string;
}

export interface RuleDTO {
  entrypoint: string;
  patterns: PatternDTO[];
}

export interface YALexFileResult {
  header: string;
  definitions: LetDefinitionDTO[];
  rules: RuleDTO[];
  trailer: string;
}

export interface DFAGraphNode {
  id: string;
  label: string;
  accept: boolean;
  start: boolean;
}

export interface DFAGraphEdge {
  id: string;
  source: string;
  target: string;
  symbols: string[];   // individual transition characters
}

export interface DFAGraphData {
  nodes: DFAGraphNode[];
  edges: DFAGraphEdge[];
}

export interface LexerOutput {
  lines: string[];
  error?: string;
}

export interface ParserTokenDef {
  name: string;
  id: number;
}

export interface ParserProduction {
  name: string;
  rules: string[][];
}

export interface ParserBuildResult {
  tokens: ParserTokenDef[];
  productions: ParserProduction[];
  ignoreList: string[];
}

export interface LR0Node {
  id: string;
  label: string;
  items: string[];
  isStart: boolean;
  isAccept: boolean;
}

export interface LR0Edge {
  id: string;
  source: string;
  target: string;
  symbol: string;
}

export interface LR0GraphData {
  nodes: LR0Node[];
  edges: LR0Edge[];
}

export interface RunOutput {
  lines: string[];
}

export interface SLRConflict {
  state: number;
  symbol: string;
  existing: string;
  incoming: string;
}

export interface SLRProduction {
  head: string;
  body: string;
}

export interface SLRData {
  terminals: string[];
  nonTerminals: string[];
  actions: Record<number, Record<string, string>>;
  gotos: Record<number, Record<string, number>>;
  conflicts: SLRConflict[];
  first: Record<string, string[]>;
  follow: Record<string, string[]>;
  productions: SLRProduction[];
  startSymbol: string;
  stateCount: number;
}

export interface EditorTab {
  path: string;
  label: string;
  content: string;
  isDirty: boolean;
  /** Populated when the tab is a .dfa.json file — renders DFA viewer instead of Monaco. */
  dfaData?: DFAGraphData;
  /** Populated when the tab is a .lr0.json file — renders LR0 viewer instead of Monaco. */
  lr0Data?: LR0GraphData;
  /** Populated after Build Parser — renders SLR table + FIRST/FOLLOW viewer. */
  slrData?: SLRData;
}
