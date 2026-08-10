import { useState, useCallback, useEffect, useRef } from "react";
import FileExplorer from "./components/Sidebar/FileExplorer";
import EditorPane from "./components/Editor/EditorPane";
import TerminalPane from "./components/Terminal/TerminalPane";
import StatusBar from "./components/StatusBar/StatusBar";
import type { FileNode, EditorTab } from "./types";
import { api } from "./api";
import "./App.css";
 
export default function App() {
  const [fileTree, setFileTree] = useState<FileNode[]>([]);
  const [tabs, setTabs] = useState<EditorTab[]>([]);
  const [activeTab, setActiveTab] = useState<string | null>(null);
  const [terminalLines, setTerminalLines] = useState<string[]>(["Compiscript IDE ready."]);
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
      setTabs((prev) => [...prev, { path: node.path, label: node.name, content, isDirty: false }]);
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
    if (!tab || tab.treeData) return; // tree tabs are read-only
    try {
      await api.writeFile(path, tab.content);
      setTabs((prev) => prev.map((t) => t.path === path ? { ...t, isDirty: false } : t));
      appendTerminal(`Saved ${path}`);
      await refreshTree(); // file may be new; keep explorer in sync
    } catch (e: any) {
      appendTerminal(`Save error: ${e.message}`);
    }
  }, [tabs, appendTerminal, refreshTree]);
 
  // ── Run (lex + parse) ─────────────────────────────────────────────────────────
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
 
    appendTerminal(`\n▶ Running ${inputPath}`);
    try {
      const result = await api.run(inputPath);
      result.lines.forEach((l) => appendTerminal(l));
      appendTerminal(`── salida guardada en output/${inputPath.split("/").pop()}.out ──`);
 
      if (result.tree) {
        const base = inputPath.split("/").pop()?.replace(/\.cps$/, "") ?? "unknown";
        const treeTabPath = `${inputPath}::tree`;
        setTabs((prev) => {
          const idx = prev.findIndex((t) => t.path === treeTabPath);
          const treeTab: EditorTab = {
            path: treeTabPath, label: `${base} tree`, content: "", isDirty: false, treeData: result.tree!,
          };
          if (idx >= 0) { const n = [...prev]; n[idx] = treeTab; return n; }
          return [...prev, treeTab];
        });
        setActiveTab(treeTabPath);
      }
 
      await refreshTree();
    } catch (e: any) {
      appendTerminal(`Error: ${e.message}`);
    }
  }, [tabs, appendTerminal, refreshTree]);
 
  const activeTabData = tabs.find((t) => t.path === activeTab) ?? null;
  const isCps = (activeTab?.endsWith(".cps") ?? false) && !activeTabData?.treeData;
 
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
          onRunFile={isCps ? runFile : undefined}
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
