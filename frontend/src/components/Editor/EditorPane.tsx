import MonacoEditor from "@monaco-editor/react";
import type * as Monaco from "monaco-editor";
import type { EditorTab } from "../../types";
import { registerYALLanguage, registerOutLanguage, registerYALPLanguage } from "../../lib/monaco-yal";
import DFAViewer from "../DFAViewer/DFAViewer";
import LR0Viewer from "../LR0Viewer/LR0Viewer";
import SLRViewer from "../SLRViewer/SLRViewer";
import MarkdownViewer from "../MarkdownViewer/MarkdownViewer";
import "./Editor.css";

interface Props {
  tabs: EditorTab[];
  activeTab: string | null;
  onSelectTab: (p: string) => void;
  onCloseTab: (p: string) => void;
  onChangeContent: (p: string, c: string) => void;
  onSave: (p: string) => void;
  onBuildDFA?: (p: string) => void;
  onBuildParser?: (p: string) => void;
  onRunFile?: (p: string) => void;
}

export default function EditorPane({
  tabs, activeTab, onSelectTab, onCloseTab, onChangeContent, onSave, onBuildDFA, onBuildParser, onRunFile,
}: Props) {
  const active = tabs.find((t) => t.path === activeTab) ?? null;
  const isYAL  = activeTab?.endsWith(".yal") ?? false;
  const isYALP = activeTab?.endsWith(".yalp") ?? false;
  const isInput = !!onRunFile;
  const isDFATab = !!(active?.dfaData);
  const isLR0Tab = !!(active?.lr0Data);
  const isSLRTab = !!(active?.slrData);
  const isMarkdown = activeTab?.endsWith(".md") ?? false;

  const handleBeforeMount = (monaco: typeof Monaco) => {
    registerYALLanguage(monaco);
    registerYALPLanguage(monaco);
    registerOutLanguage(monaco);
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
            {isYAL && (
              <button className="toolbar-pill" onClick={() => onBuildDFA?.(activeTab!)}>
                ◎ Build Lexer
              </button>
            )}
            {isYALP && (
              <button className="toolbar-pill toolbar-pill--parser" onClick={() => onBuildParser?.(activeTab!)}>
                ◎ Build Parser
              </button>
            )}
            {isInput && (
              <button className="toolbar-pill toolbar-pill--run" onClick={() => onRunFile?.(activeTab!)}>
                ▶ Run
              </button>
            )}
          </div>
        </div>
      )}

      {/* Editor / DFA viewer / welcome */}
      <div className="editor-body">
        {active ? (
          active.dfaData ? (
            <DFAViewer data={active.dfaData} />
          ) : active.lr0Data ? (
            <LR0Viewer data={active.lr0Data} />
          ) : active.slrData ? (
            <SLRViewer data={active.slrData} />
          ) : isMarkdown ? (
            <MarkdownViewer content={active.content} />
          ) : (
            <MonacoEditor
              height="100%"
              language={getLanguage(active.path)}
              theme={
            active.path.endsWith(".out")  ? "yalex-dark-out" :
            active.path.endsWith(".yalp") ? "yapar-dark" :
            "yalex-dark"
          }
              value={active.content}
              beforeMount={handleBeforeMount}
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
      <div className="editor-welcome__badge">YAPar</div>
      <p className="editor-welcome__sub">Parser Generator</p>
      <div className="editor-welcome__hints">
        <Hint keys={["Ctrl", "S"]} label="Force save (auto-saves after 800ms)" />
        <Hint keys={["◎ Build DFA"]} label="Generate automaton from .yal" />
        <Hint keys={["▶ Run"]} label="Test lexer on input" />
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
  if (path.endsWith(".yal"))  return "yalex";
  if (path.endsWith(".yalp")) return "yapar";
  if (path.endsWith(".out"))  return "lexout";
  if (path.endsWith(".go"))   return "go";
  if (path.endsWith(".json")) return "json";
  if (path.endsWith(".ts") || path.endsWith(".tsx")) return "typescript";
  if (path.endsWith(".js"))   return "javascript";
  if (path.endsWith(".md"))   return "markdown";
  return "plaintext";
}
