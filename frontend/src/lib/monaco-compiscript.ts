import type * as Monaco from "monaco-editor";

const KEYWORDS = [
  "let", "var", "const", "print", "if", "else", "while", "do", "for",
  "foreach", "in", "break", "continue", "return", "try", "catch", "switch",
  "case", "default", "function", "class", "new", "this", "null", "true",
  "false",
];

const TYPE_KEYWORDS = ["boolean", "integer", "string"];

/**
 * Registers the "compiscript" language with Monaco for .cps files —
 * syntax highlighting for keywords, types, comments, strings and numbers.
 */
export function registerCompiscriptLanguage(monaco: typeof Monaco) {
  if (monaco.languages.getLanguages().some((l) => l.id === "compiscript")) return;

  monaco.languages.register({ id: "compiscript", extensions: [".cps"] });

  monaco.languages.setMonarchTokensProvider("compiscript", {
    keywords: KEYWORDS,
    typeKeywords: TYPE_KEYWORDS,
    tokenizer: {
      root: [
        [/\/\/.*$/, "comment"],
        [/\/\*/, "comment", "@comment"],
        [/"([^"\\]|\\.)*"/, "string"],
        [/\b\d+(\.\d+)?\b/, "number"],
        [new RegExp(`\\b(${TYPE_KEYWORDS.join("|")})\\b`), "type"],
        [new RegExp(`\\b(${KEYWORDS.join("|")})\\b`), "keyword"],
        [/[a-zA-Z_][a-zA-Z0-9_]*/, "identifier"],
        [/[{}()\[\]]/, "@brackets"],
        [/[<>=!]=|&&|\|\||[+\-*/%<>=!]/, "operator"],
        [/[;,.:?]/, "delimiter"],
        [/\s+/, "white"],
      ],
      comment: [
        [/\*\//, "comment", "@pop"],
        [/[^*/]+/, "comment"],
        [/[*/]/, "comment"],
      ],
    },
  });

  monaco.languages.setLanguageConfiguration("compiscript", {
    comments: { lineComment: "//", blockComment: ["/*", "*/"] },
    brackets: [["(", ")"], ["[", "]"], ["{", "}"]],
    autoClosingPairs: [
      { open: "(", close: ")" },
      { open: "[", close: "]" },
      { open: "{", close: "}" },
      { open: '"', close: '"' },
    ],
    surroundingPairs: [
      { open: "(", close: ")" },
      { open: "[", close: "]" },
      { open: '"', close: '"' },
    ],
  });

  monaco.editor.defineTheme("compiscript-dark", {
    base: "vs-dark",
    inherit: true,
    rules: [
      { token: "keyword",  foreground: "c792ea", fontStyle: "bold" },
      { token: "type",     foreground: "f78c6c", fontStyle: "bold" },
      { token: "comment",  foreground: "546e7a", fontStyle: "italic" },
      { token: "string",   foreground: "c3e88d" },
      { token: "number",   foreground: "f78c6c" },
      { token: "operator", foreground: "89ddff" },
      { token: "identifier", foreground: "82aaff" },
    ],
    colors: {
      "editor.background":           "#14141a",
      "editor.foreground":           "#e2e2e6",
      "editorLineNumber.foreground": "#3a3a4a",
      "editorLineNumber.activeForeground": "#7c6af7",
      "editor.lineHighlightBackground": "#1c1c26",
      "editorCursor.foreground":     "#8b5cf6",
      "editor.selectionBackground":  "#3b3170",
      "editor.inactiveSelectionBackground": "#2a2550",
      "editorIndentGuide.background1": "#2a2a36",
      "editorIndentGuide.activeBackground1": "#8b5cf6",
    },
  });
}

/**
 * Registers the "cpsout" language for the .out files written by /api/run —
 * highlights the Spanish "Error léxico"/"Error sintáctico" lines produced by
 * error_listener.py, plus the trailing summary/success line.
 */
export function registerOutputLanguage(monaco: typeof Monaco) {
  if (monaco.languages.getLanguages().some((l) => l.id === "cpsout")) return;

  monaco.languages.register({ id: "cpsout", extensions: [".out"] });

  monaco.languages.setMonarchTokensProvider("cpsout", {
    tokenizer: {
      root: [
        [/^Error léxico\b.*$/, "out.lexical"],
        [/^Error sintáctico\b.*$/, "out.syntax"],
        [/^Se encontraron .*$/, "out.summary"],
        [/^El archivo fue analizado correctamente\..*$/, "out.success"],
        [/^No se encontraron errores.*$/, "out.success"],
        [/\bl[ií]nea \d+, columna \d+\b/, "out.location"],
        [/'[^']*'/, "out.token"],
        [/\s+/, "white"],
      ],
    },
  });

  monaco.editor.defineTheme("compiscript-dark-out", {
    base: "vs-dark",
    inherit: true,
    rules: [
      { token: "out.lexical",  foreground: "f87171", fontStyle: "bold" },
      { token: "out.syntax",   foreground: "fb923c", fontStyle: "bold" },
      { token: "out.summary",  foreground: "fbbf24", fontStyle: "italic" },
      { token: "out.success",  foreground: "4ade80", fontStyle: "bold" },
      { token: "out.location", foreground: "89ddff" },
      { token: "out.token",    foreground: "c3e88d" },
    ],
    colors: {
      "editor.background":           "#14141a",
      "editor.foreground":           "#e2e2e6",
      "editorLineNumber.foreground": "#3a3a4a",
      "editorLineNumber.activeForeground": "#7c6af7",
      "editor.lineHighlightBackground": "#1c1c26",
      "editorCursor.foreground":     "#8b5cf6",
      "editor.selectionBackground":  "#3b3170",
    },
  });
}
