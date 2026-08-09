import { useState, useCallback, useEffect, useRef } from "react";
import FileExplorer from "./components/Sidebar/FileExplorer";
import EditorPane from "./components/Editor/EditorPane";
import TerminalPane from "./components/Terminal/TerminalPane";
import StatusBar from "./components/StatusBar/StatusBar";
import type { FileNode, DFAGraphData, LR0GraphData, SLRData, EditorTab } from "./types";
import { api } from "./api";
import "./App.css";

export default function App() {
  const [fileTree, setFileTree] = useState<FileNode[]>([]);
  const [tabs, setTabs] = useState<EditorTab[]>([]);
  const [activeTab, setActiveTab] = useState<string | null>(null);
  const [terminalLines, setTerminalLines] = useState<string[]>(["YAPar ready."]);
  const [terminalHeight, setTerminalHeight] = useState(200);
  const resizing = useRef(false);
  const resizeStartY = useRef(0);
  const resizeStartH = useRef(0);
  const autoSaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const appendTerminal = useCallback((line: string) => {
    setTerminalLines((prev) => [...prev, line]);
  }, []);

  const refreshTree = useCallback(async () => {
    try {
      const tree = await api.listDirectory();
      setFileTree(tree);
    } catch (e: any) {
      appendTerminal(`Error refreshing tree: ${e.message}`);
    }
  }, [appendTerminal]);

  useEffect(() => { refreshTree(); }, []);

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!resizing.current) return;
      const delta = resizeStartY.current - e.clientY;
      const next = Math.max(60, Math.min(resizeStartH.current + delta, window.innerHeight * 0.75));
      setTerminalHeight(next);
    };
    const onUp = () => { resizing.current = false; document.body.style.cursor = ""; };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => { window.removeEventListener("mousemove", onMove); window.removeEventListener("mouseup", onUp); };
  }, []);

  const onResizeStart = useCallback((e: React.MouseEvent) => {
    resizing.current = true;
    resizeStartY.current = e.clientY;
    resizeStartH.current = terminalHeight;
    document.body.style.cursor = "ns-resize";
    e.preventDefault();
  }, [terminalHeight]);

  // ── File ops ────────────────────────────────────────────────────────────────
  const openFile = useCallback(async (node: FileNode) => {
    if (node.isDir) return;
    const existing = tabs.find((t) => t.path === node.path);
    if (existing) { setActiveTab(node.path); return; }
    try {
      const content = await api.readFile(node.path);
      // Parse .dfa.json files as DFA graph data — rendered as DFA viewer, not Monaco.
      let dfaData: DFAGraphData | undefined;
      let lr0Data: LR0GraphData | undefined;
      let slrData: SLRData | undefined;
      let label = node.name;
      if (node.name === "dfa.json" || node.path.endsWith(".dfa.json") || node.path.endsWith(".dfa")) {
        try { dfaData = JSON.parse(content) as DFAGraphData; } catch { /* fall through */ }
        label = node.path.split("/").slice(-2, -1)[0] + " DFA";
      } else if (node.name === "lr0.json" || node.path.endsWith(".lr0.json") || node.path.endsWith(".lr0")) {
        try { lr0Data = JSON.parse(content) as LR0GraphData; } catch { /* fall through */ }
        label = node.path.split("/").slice(-2, -1)[0] + " LR(0)";
      } else if (node.name === "slr.json" || node.path.endsWith(".slr.json") || node.path.endsWith(".slr")) {
        try { slrData = JSON.parse(content) as SLRData; } catch { /* fall through */ }
        label = node.path.split("/").slice(-2, -1)[0] + " SLR";
      }
      setTabs((prev) => [...prev, { path: node.path, label, content, isDirty: false, dfaData, lr0Data, slrData }]);
      setActiveTab(node.path);
    } catch (e: any) {
      appendTerminal(`Error opening ${node.path}: ${e.message}`);
    }
  }, [tabs, appendTerminal]);

  const closeTab = useCallback((path: string) => {
    setTabs((prev) => {
      const next = prev.filter((t) => t.path !== path);
      setActiveTab((cur) => {
        if (cur !== path) return cur;
        return next.length > 0 ? next[next.length - 1].path : null;
      });
      return next;
    });
  }, []);

  const updateTabContent = useCallback((path: string, content: string) => {
    setTabs((prev) => prev.map((t) => t.path === path ? { ...t, content, isDirty: true } : t));
    if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);
    autoSaveTimer.current = setTimeout(async () => {
      try {
        await api.writeFile(path, content);
        setTabs((prev) => prev.map((t) => t.path === path ? { ...t, isDirty: false } : t));
      } catch { /* silent — user can still Ctrl+S manually */ }
    }, 200);
  }, []);

  const saveTab = useCallback(async (path: string) => {
    const tab = tabs.find((t) => t.path === path);
    if (!tab || tab.dfaData || tab.path.endsWith(".dfa")) return; // DFA tabs are read-only
    try {
      await api.writeFile(path, tab.content);
      setTabs((prev) => prev.map((t) => t.path === path ? { ...t, isDirty: false } : t));
      appendTerminal(`Saved ${path}`);
      await refreshTree(); // file may be new; keep explorer in sync
    } catch (e: any) {
      appendTerminal(`Save error: ${e.message}`);
    }
  }, [tabs, appendTerminal, refreshTree]);

  // ── DFA ─────────────────────────────────────────────────────────────────────
  // Builds the DFA, writes programs/<name>/lexer.go and programs/<name>/dfa.json.
  const buildDFA = useCallback(async (yalPath: string) => {
    appendTerminal(`Building lexer from ${yalPath}…`);
    try {
      const data = await api.getDFA(yalPath);
      appendTerminal(`Lexer built: ${data.nodes.length} states, ${data.edges.length} transitions.`);

      const base       = yalPath.split("/").pop()?.replace(/\.yal$/, "") ?? "unknown";
      const dfaTabPath = `programs/${base}/docs/dfa.json`;
      const lexerPath  = `programs/${base}/lexer/lexer.go`;

      await refreshTree();

      let lexerContent = "";
      try { lexerContent = await api.readFile(lexerPath); } catch { /* ok */ }

      setTabs((prev) => {
        const upsert = (arr: EditorTab[], tab: EditorTab) => {
          const idx = arr.findIndex((t) => t.path === tab.path);
          if (idx >= 0) { const n = [...arr]; n[idx] = tab; return n; }
          return [...arr, tab];
        };
        let next = upsert(prev, {
          path: dfaTabPath, label: `${base} DFA`, content: "", isDirty: false, dfaData: data,
        });
        next = upsert(next, {
          path: lexerPath, label: `${base}/lexer.go`, content: lexerContent, isDirty: false,
        });
        return next;
      });
      setActiveTab(dfaTabPath);
    } catch (e: any) {
      appendTerminal(`Build error: ${e.message}`);
    }
  }, [appendTerminal, refreshTree]);

  // ── Parser build ──────────────────────────────────────────────────────────────
  const buildParser = useCallback(async (yalpPath: string) => {
    appendTerminal(`\nBuilding grammar from ${yalpPath}…`);
    try {
      const result = await api.buildParser(yalpPath);

      const base = yalpPath.split("/").pop()?.replace(/\.yalp$/, "") ?? "unknown";

      const upsert = (prev: EditorTab[], tab: EditorTab) => {
        const idx = prev.findIndex((t) => t.path === tab.path);
        if (idx >= 0) { const n = [...prev]; n[idx] = tab; return n; }
        return [...prev, tab];
      };

      // Extract SLR data from the response and open the SLR viewer tab.
      const slrData: SLRData = {
        terminals:    result.terminals,
        nonTerminals: result.nonTerminals,
        actions:      result.actions,
        gotos:        result.gotos,
        conflicts:    result.conflicts,
        first:        result.first,
        follow:       result.follow,
        productions:  result.productions,
        startSymbol:  result.startSymbol,
        stateCount:   result.stateCount,
      };
      const slrTabPath = `programs/${base}/docs/slr.json`;
      setTabs((prev) => upsert(prev, {
        path: slrTabPath, label: `${base} SLR`, content: "", isDirty: false, slrData,
      }));
      setActiveTab(slrTabPath);

      // Also open the LR(0) graph tab in the background.
      const lr0JsonPath = `programs/${base}/docs/lr0.json`;
      try {
        const raw     = await api.readFile(lr0JsonPath);
        const lr0Data = JSON.parse(raw) as LR0GraphData;
        setTabs((prev) => upsert(prev, {
          path: lr0JsonPath, label: `${base} LR(0)`, content: "", isDirty: false, lr0Data,
        }));
      } catch { /* not critical */ }

      await refreshTree();
    } catch (e: any) {
      appendTerminal(`Parser error: ${e.message}`);
    }
  }, [appendTerminal, refreshTree]);

  // ── Run (parser-aware) ────────────────────────────────────────────────────────
  const runFile = useCallback(async (inputPath: string) => {
    const tab = tabs.find((t) => t.path === inputPath);
    if (tab?.isDirty) {
      try {
        await api.writeFile(inputPath, tab.content);
        setTabs((prev) => prev.map((t) => t.path === inputPath ? { ...t, isDirty: false } : t));
      } catch (e: any) {
        appendTerminal(`Save error: ${e.message}`);
        return;
      }
    }

    const ext = inputPath.split(".").pop() ?? "";
    appendTerminal(`\n▶ Running ${inputPath} (spec: ${ext})`);
    try {
      const result = await api.run(inputPath);
      (result.lines ?? []).forEach((l) => appendTerminal(l));
      appendTerminal(`── output saved to output/${inputPath.split("/").pop()}.out ──`);
      refreshTree();
    } catch (e: any) {
      appendTerminal(`Error: ${e.message}`);
    }
  }, [tabs, appendTerminal, refreshTree]);

  const activeTabData = tabs.find((t) => t.path === activeTab) ?? null;
  const isYAL  = activeTab?.endsWith(".yal") ?? false;
  const isYALP = activeTab?.endsWith(".yalp") ?? false;
  const isInput = activeTab?.startsWith("input/") ?? false;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <FileExplorer
          tree={fileTree}
          activeFile={activeTab}
          onOpenFile={openFile}
          onRefresh={refreshTree}
          appendTerminal={appendTerminal}
          refreshTree={refreshTree}
        />
      </aside>

      <div className="main-area">
        <EditorPane
          tabs={tabs}
          activeTab={activeTab}
          onSelectTab={setActiveTab}
          onCloseTab={closeTab}
          onChangeContent={updateTabContent}
          onSave={saveTab}
          onBuildDFA={isYAL ? buildDFA : undefined}
          onBuildParser={isYALP ? buildParser : undefined}
          onRunFile={isInput ? runFile : undefined}
        />
        <div className="resize-handle" onMouseDown={onResizeStart} />
        <TerminalPane
            lines={terminalLines}
            onClear={() => setTerminalLines([])}
            height={terminalHeight}
          />
      </div>

      <StatusBar
        activeFile={activeTabData?.path ?? null}
        isDirty={activeTabData?.isDirty ?? false}
      />
    </div>
  );
}
