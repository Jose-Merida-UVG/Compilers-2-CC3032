import MonacoEditor from "@monaco-editor/react";
import type * as Monaco from "monaco-editor";
import type { EditorTab, EditorLocation } from "../../types";
import { registerCompiscriptLanguage, registerOutputLanguage } from "../../lib/monaco-compiscript";
import ParseTreeViewer from "../ParseTreeViewer/ParseTreeViewer";
import SymbolTableViewer from "../SymbolTableViewer/SymbolTableViewer";
import TacViewer from "../TacViewer/TacViewer";
import MarkdownViewer from "../MarkdownViewer/MarkdownViewer";
import { useEffect, useRef } from "react";
import "./Editor.css";

interface Props {
  tabs: EditorTab[];
  activeTab: string | null;
  onSelectTab: (p: string) => void;
  onCloseTab: (p: string) => void;
  onChangeContent: (p: string, c: string) => void;
  onSave: (p: string) => void;
  onRunFile?: (p: string) => void;
  location?: EditorLocation | null;
}

export default function EditorPane({
  tabs, activeTab, onSelectTab, onCloseTab, onChangeContent, onSave, onRunFile, location,
}: Props) {
  const active = tabs.find((t) => t.path === activeTab) ?? null;
  const isRunnable = !!onRunFile;
  const isTreeTab = !!(active?.treeData);
  const isSymbolTableTab = !!(active?.symbolTableData);
  const isTacTab = !!(active?.tacData);
  const isMarkdown = activeTab?.endsWith(".md") ?? false;
  const editorRef = useRef<Monaco.editor.IStandaloneCodeEditor | null>(null);

  const revealLocation = (editor: Monaco.editor.IStandaloneCodeEditor) => {
    if (!location || location.path !== activeTab) return;

    const model = editor.getModel();
    if (!model) return;

    const position = model.validatePosition({
      lineNumber: location.line,
      column: location.column,
    });

    editor.setPosition(position);
    editor.revealLineInCenter(position.lineNumber);
    editor.focus();
  };

  useEffect(() => {
    if (isTreeTab || isSymbolTableTab || isTacTab || isMarkdown) return;

    const frame = requestAnimationFrame(() => {
      if (editorRef.current) {
        revealLocation(editorRef.current);
      }
    });

    return () => cancelAnimationFrame(frame);
  }, [location, activeTab, isTreeTab, isSymbolTableTab, isTacTab, isMarkdown]);

  const handleBeforeMount = (monaco: typeof Monaco) => {
    registerCompiscriptLanguage(monaco);
    registerOutputLanguage(monaco);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "s") {
      e.preventDefault();
      if (activeTab) onSave(activeTab);
    }
  };

  return (
    <div className="editor-pane" onKeyDown={handleKeyDown}>
      {/* Tab bar */}
      {tabs.length > 0 && (
        <div className="tab-bar">
          {tabs.map((tab) => (
            <div
              key={tab.path}
              className={`tab ${tab.path === activeTab ? "active" : ""}`}
              onClick={() => onSelectTab(tab.path)}
            >
              <span className="tab__label">{tab.label}</span>
              <button
                className="tab__close"
                onClick={(e) => { e.stopPropagation(); onCloseTab(tab.path); }}
              >×</button>
            </div>
          ))}
        </div>
      )}

      {/* Breadcrumb / toolbar */}
      {active && (
        <div className="editor-toolbar">
          <span className="editor-toolbar__path">{active.path}</span>
          <div className="editor-toolbar__actions">
            {isRunnable && (
              <button className="toolbar-pill toolbar-pill--run" onClick={() => onRunFile?.(activeTab!)}>
                ▶ Compilar
              </button>
            )}
          </div>
        </div>
      )}

      {/* Editor / tree viewer / welcome */}
      <div className="editor-body">
        {active ? (
          isTreeTab ? (
            <ParseTreeViewer data={active.treeData!} />
          ) : isSymbolTableTab ? (
            <SymbolTableViewer data={active.symbolTableData!} />
          ) : isTacTab ? (
            <TacViewer data={active.tacData!} />
          ) : isMarkdown ? (
            <MarkdownViewer content={active.content} />
          ) : (
            <MonacoEditor
              height="100%"
              language={getLanguage(active.path)}
              theme={active.path.endsWith(".out") ? "compiscript-dark-out" : "compiscript-dark"}
              value={active.content}
              beforeMount={handleBeforeMount}
              onMount={(editor) => {
                editorRef.current = editor;
                revealLocation(editor);
              }}
              onChange={(val) => { if (val !== undefined) onChangeContent(active.path, val); }}
              options={{
                fontSize: 12,
                lineHeight: 22,
                fontFamily: '"JetBrains Mono", "Cascadia Code", "Fira Code", monospace',
                fontLigatures: true,
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                wordWrap: "on",
                automaticLayout: true,
                tabSize: 2,
                renderWhitespace: "selection",
                smoothScrolling: true,
                cursorBlinking: "smooth",
                cursorSmoothCaretAnimation: "on",
                padding: { top: 12, bottom: 12 },
                bracketPairColorization: { enabled: true },
                guides: { bracketPairs: true, indentation: true },
                suggest: { showKeywords: true },
              }}
            />
          )
        ) : (
          <Welcome />
        )}
      </div>
    </div>
  );
}

function Welcome() {
  return (
    <div className="editor-welcome">
      <div className="editor-welcome__badge">Compiscript</div>
      <p className="editor-welcome__sub">Lexical, Syntax &amp; Semantic Analysis · Intermediate Code (TAC)</p>
      <div className="editor-welcome__hints">
        <Hint keys={["Ctrl", "S"]} label="Force save (auto-saves after 200ms)" />
        <Hint keys={["▶ Compilar"]} label="Analiza el archivo .cps: errores, árbol sintáctico, tabla de símbolos y TAC" />
      </div>
    </div>
  );
}

function Hint({ keys, label }: { keys: string[]; label: string }) {
  return (
    <div className="welcome-hint">
      <div className="welcome-hint__keys">
        {keys.map((k) => <kbd key={k}>{k}</kbd>)}
      </div>
      <span className="welcome-hint__label">{label}</span>
    </div>
  );
}

function getLanguage(path: string): string {
  if (path.endsWith(".cps")) return "compiscript";
  if (path.endsWith(".out")) return "cpsout";
  if (path.endsWith(".json")) return "json";
  if (path.endsWith(".ts") || path.endsWith(".tsx")) return "typescript";
  if (path.endsWith(".js")) return "javascript";
  if (path.endsWith(".md")) return "markdown";
  return "plaintext";
}
