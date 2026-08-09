import type * as Monaco from "monaco-editor";

/**
 * Registers the "yalex" language with Monaco for .yal files.
 * Provides syntax highlighting for keywords, comments, strings, and operators.
 */
export function registerOutLanguage(monaco: typeof Monaco) {
  if (monaco.languages.getLanguages().some((l) => l.id === "lexout")) return;

  monaco.languages.register({ id: "lexout", extensions: [".out"] });

  monaco.languages.setMonarchTokensProvider("lexout", {
    tokenizer: {
      root: [
        // ERROR lines
        [/^ERROR\b.*$/, "out.error"],
        // token name at start of line (all caps word)
        [/^[A-Z][A-Z0-9_]+/, "out.token"],
        // quoted lexeme
        [/"[^"]*"/, "out.lexeme"],
        // ln= col= labels
        [/\b(ln|col)=/, "out.label"],
        // numbers (line/col values and ranges like 5-6)
        [/\d+(-\d+)?/, "out.number"],
        [/\s+/, "white"],
      ],
    },
  });

  // Rules are added into the existing yalex-dark theme via addExtraTokenThemeRules
  monaco.editor.defineTheme("yalex-dark-out", {
    base: "vs-dark",
    inherit: true,
    rules: [
      { token: "out.error",  foreground: "f87171", fontStyle: "bold" },
      { token: "out.token",  foreground: "4ade80", fontStyle: "bold" },
      { token: "out.lexeme", foreground: "fbbf24" },
      { token: "out.label",  foreground: "546e7a" },
      { token: "out.number", foreground: "89ddff" },
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

export function registerYALPLanguage(monaco: typeof Monaco) {
  if (monaco.languages.getLanguages().some((l) => l.id === "yapar")) return;

  monaco.languages.register({ id: "yapar", extensions: [".yalp"] });

  monaco.languages.setMonarchTokensProvider("yapar", {
    tokenizer: {
      root: [
        // Block comments /* ... */
        [/\/\*/, "comment", "@comment"],
        // %% section separator — own style
        [/%%/, "separator"],
        // Directives
        [/%token/, "directive"],
        [/\bIGNORE\b/, "directive"],
        // Token names (UPPERCASE) — terminals
        [/\b[A-Z][A-Z0-9_]*\b/, "terminal"],
        // Production head: non-terminal immediately followed by :
        [/\b[a-z][a-z0-9_]*(?=\s*:)/, "prodhead"],
        // Non-terminal names in body (lowercase)
        [/\b[a-z][a-z0-9_]*\b/, "nonterminal"],
        // Semicolon ends a production
        [/;/, "endrule"],
        // Colon and pipe
        [/[:|]/, "operator"],
        [/\s+/, "white"],
      ],
      comment: [
        [/\*\//, "comment", "@pop"],
        [/[^*/]+/, "comment"],
        [/[*/]/, "comment"],
      ],
    },
  });

  monaco.languages.setLanguageConfiguration("yapar", {
    comments: { blockComment: ["/*", "*/"] },
    brackets: [["(", ")"]],
  });

  monaco.editor.defineTheme("yapar-dark", {
    base: "vs-dark",
    inherit: true,
    rules: [
      { token: "directive",   foreground: "c792ea", fontStyle: "bold" },
      { token: "separator",   foreground: "f07178", fontStyle: "bold" },
      { token: "comment",     foreground: "546e7a", fontStyle: "italic" },
      { token: "terminal",    foreground: "f78c6c", fontStyle: "bold" },
      { token: "prodhead",    foreground: "82aaff", fontStyle: "bold" },
      { token: "nonterminal", foreground: "82aaff" },
      { token: "endrule",     foreground: "f07178", fontStyle: "bold" },
      { token: "operator",    foreground: "89ddff" },
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

export function registerYALLanguage(monaco: typeof Monaco) {
  if (monaco.languages.getLanguages().some((l) => l.id === "yalex")) return;

  monaco.languages.register({ id: "yalex", extensions: [".yal"] });

  monaco.languages.setMonarchTokensProvider("yalex", {
    keywords: ["let", "rule", "eof", "raise", "return"],
    tokenizer: {
      root: [
        // Block comments (* ... *) — support nesting via state
        [/\(\*/, "comment", "@comment"],
        // Single-quoted chars/strings
        [/'[^']*'/, "string"],
        // Double-quoted strings
        [/"[^"]*"/, "string"],
        // Keywords
        [/\b(let|rule|eof|raise|return)\b/, "keyword"],
        // Named identifiers (after let / inside rules)
        [/[a-zA-Z_][a-zA-Z0-9_]*/, "identifier"],
        // Regex operators
        [/[|*+?()\[\]{}\\]/, "regexp"],
        // Range separator
        [/'-'/, "string"],
        // Equals sign
        [/=/, "operator"],
        // Whitespace
        [/\s+/, "white"],
      ],
      comment: [
        [/\*\)/, "comment", "@pop"],
        [/\(\*/, "comment", "@push"],   // nested comments
        [/[^(*]+/, "comment"],
        [/[(*]/, "comment"],
      ],
    },
  });

  monaco.languages.setLanguageConfiguration("yalex", {
    comments: { blockComment: ["(*", "*)"] },
    brackets: [
      ["(", ")"],
      ["[", "]"],
      ["{", "}"],
    ],
    autoClosingPairs: [
      { open: "(", close: ")" },
      { open: "[", close: "]" },
      { open: "{", close: "}" },
      { open: "'", close: "'" },
      { open: '"', close: '"' },
    ],
    surroundingPairs: [
      { open: "(", close: ")" },
      { open: "[", close: "]" },
      { open: "'", close: "'" },
    ],
  });

  // Dark theme that fits our UI
  monaco.editor.defineTheme("yalex-dark", {
    base: "vs-dark",
    inherit: true,
    rules: [
      { token: "keyword",    foreground: "c792ea", fontStyle: "bold" },
      { token: "comment",    foreground: "546e7a", fontStyle: "italic" },
      { token: "string",     foreground: "c3e88d" },
      { token: "regexp",     foreground: "89ddff" },
      { token: "operator",   foreground: "89ddff" },
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
