import { useState, useCallback, useEffect, useRef, Fragment } from "react";
import FileExplorer from "./components/Sidebar/FileExplorer";
import EditorPane from "./components/Editor/EditorPane";
import TerminalPane from "./components/Terminal/TerminalPane";
import StatusBar from "./components/StatusBar/StatusBar";
import type { FileNode, EditorTab, CompilerDiagnostic, EditorLocation } from "./types";
import { api } from "./api";
import "./App.css";
 
type Pane = 0 | 1;

export default function App() {
  const [fileTree, setFileTree] = useState<FileNode[]>([]);
  const [tabs, setTabs] = useState<EditorTab[]>([]);
  // Dos paneles de editor (izquierda/derecha). Cada pestaña pertenece a uno;
  // cada panel tiene su pestaña activa. El panel 1 solo se ve si tiene pestañas.
  const [paneOf, setPaneOf] = useState<Record<string, Pane>>({});
  const [activeByPane, setActiveByPane] = useState<[string | null, string | null]>([null, null]);
  const [focusedPane, setFocusedPane] = useState<Pane>(0);
  const [splitRatio, setSplitRatio] = useState(0.5);
  const editorAreaRef = useRef<HTMLDivElement>(null);
  const splitting = useRef(false);
  const [terminalLines, setTerminalLines] = useState<string[]>(["Compiscript IDE ready."]);
  const [terminalHeight, setTerminalHeight] = useState(200);
  const resizing = useRef(false);
  const resizeStartY = useRef(0);
  const resizeStartH = useRef(0);
  const autoSaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [tacNotice, setTacNotice] = useState<string | null>(null);
  const [diagnostics, setDiagnostics] = useState<CompilerDiagnostic[]>([]);
  const [editorLocation, setEditorLocation] = useState<EditorLocation | null>(null);
 
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
      if (splitting.current && editorAreaRef.current) {
        const box = editorAreaRef.current.getBoundingClientRect();
        setSplitRatio(Math.max(0.2, Math.min((e.clientX - box.left) / box.width, 0.8)));
        return;
      }
      if (!resizing.current) return;
      const delta = resizeStartY.current - e.clientY;
      const next = Math.max(60, Math.min(resizeStartH.current + delta, window.innerHeight * 0.75));
      setTerminalHeight(next);
    };
    const onUp = () => {
      resizing.current = false;
      splitting.current = false;
      document.body.style.cursor = "";
    };
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
 
  const onSplitStart = useCallback((e: React.MouseEvent) => {
    splitting.current = true;
    document.body.style.cursor = "ew-resize";
    e.preventDefault();
  }, []);

  const paneFor = useCallback((path: string): Pane => paneOf[path] ?? 0, [paneOf]);

  // Hace visible `path` en `pane` y le da el foco.
  const activate = useCallback((path: string, pane: Pane) => {
    setPaneOf((prev) => (prev[path] === pane ? prev : { ...prev, [path]: pane }));
    setActiveByPane((prev) => (pane === 0 ? [path, prev[1]] : [prev[0], path]));
    setFocusedPane(pane);
  }, []);

  // Si la pestaña activa de un panel ya no existe (cerrada, reemplazada), pasa a
  // la última de ese panel.
  useEffect(() => {
    setActiveByPane((prev) => {
      const next: [string | null, string | null] = [prev[0], prev[1]];
      ([0, 1] as Pane[]).forEach((p) => {
        const inPane = tabs.filter((t) => (paneOf[t.path] ?? 0) === p);
        if (!inPane.some((t) => t.path === prev[p])) next[p] = inPane[inPane.length - 1]?.path ?? null;
      });
      return next[0] === prev[0] && next[1] === prev[1] ? prev : next;
    });
  }, [tabs, paneOf]);

  // Mueve una pestaña al otro panel (si el otro está vacío, así se divide).
  const moveTab = useCallback((path: string) => {
    activate(path, paneFor(path) === 0 ? 1 : 0);
  }, [activate, paneFor]);

  // ── File ops ────────────────────────────────────────────────────────────────
  const openFile = useCallback(async (node: FileNode) => {
    if (node.isDir) return;
    const existing = tabs.find((t) => t.path === node.path);
    if (existing) { activate(node.path, paneFor(node.path)); return; }
    try {
      const content = await api.readFile(node.path);
      if (node.path.endsWith(".tree")) {
        const treeData = JSON.parse(content);
        setTabs((prev) => [...prev, { path: node.path, label: node.name, content: "", isDirty: false, treeData }]);
      } else if (node.path.endsWith(".symbols")) {
        const symbolTableData = JSON.parse(content);
        setTabs((prev) => [...prev, { path: node.path, label: node.name, content: "", isDirty: false, symbolTableData }]);
      } else if (node.path.endsWith(".tac")) {
        // El .tac guardado solo existe si la corrida no tuvo errores
        const tacData = { lines: content.replace(/\n$/, "").split("\n"), stats: null, errorCount: 0 };
        setTabs((prev) => [...prev, { path: node.path, label: node.name, content: "", isDirty: false, tacData }]);
      } else {
        setTabs((prev) => [...prev, { path: node.path, label: node.name, content, isDirty: false }]);
      }
      activate(node.path, focusedPane);
    } catch (e: any) {
      appendTerminal(`Error opening ${node.path}: ${e.message}`);
    }
  }, [tabs, appendTerminal, activate, paneFor, focusedPane]);

  const goToDiagnostic = async (diagnostic: CompilerDiagnostic) => {
    if (diagnostic.line === null || diagnostic.column === null) return;

    await openFile({
      name: diagnostic.path.split("/").pop() ?? diagnostic.path,
      path: diagnostic.path,
      isDir: false,
    });

    setEditorLocation((previous) => ({
      path: diagnostic.path,
      line: diagnostic.line!,
      column: diagnostic.column!,
      requestId: (previous?.requestId ?? 0) + 1,
    }));
  };
 
  const closeTab = useCallback((path: string) => {
    setTabs((prev) => prev.filter((t) => t.path !== path));
    setPaneOf((prev) => {
      const { [path]: _removed, ...rest } = prev;
      return rest;
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
    if (!tab || tab.treeData || tab.symbolTableData || tab.tacData) return; // pestañas de solo lectura
    try {
      await api.writeFile(path, tab.content);
      setTabs((prev) => prev.map((t) => t.path === path ? { ...t, isDirty: false } : t));
      appendTerminal(`Saved ${path}`);
      await refreshTree(); // file may be new; keep explorer in sync
    } catch (e: any) {
      appendTerminal(`Save error: ${e.message}`);
    }
  }, [tabs, appendTerminal, refreshTree]);
 
  // ── Run (léxico, sintaxis, semántica y TAC) ───────────────────────────────────
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
 
    // Fuente en su panel; los resultados (tree, symbols, tac) en el otro
    const sourcePane = paneFor(inputPath);
    const resultPane: Pane = sourcePane === 0 ? 1 : 0;

    appendTerminal(`\n▶ Compilando ${inputPath}`);
    try {
      const result = await api.run(inputPath);
      setDiagnostics(result.errors.map((message) => {
        const position = /en línea (\d+), columna (\d+):/.exec(message);

        return {
          path: inputPath,
          message,
          line: position ? Number(position[1]) : null,
          column: position ? Number(position[2]) + 1 : null,
        };
      }));
      result.lines.forEach((l) => appendTerminal(l));
      const fileName = inputPath.split("/").pop() ?? "";
      const base = fileName.replace(/\.cps$/, "");
      const saved = result.tac
        ? ".out, .tree, .symbols y .tac"
        : result.symbolTable ? ".out, .tree y .symbols" : ".out y .tree";
      appendTerminal(`── salida guardada en output/${base}/ (${saved}) ──`);

      const placeResult = (path: string) =>
        setPaneOf((prev) => (prev[path] === resultPane ? prev : { ...prev, [path]: resultPane }));

      if (result.tree) {
        const treeTabPath = `${inputPath}::tree`;
        placeResult(treeTabPath);
        setTabs((prev) => {
          const idx = prev.findIndex((t) => t.path === treeTabPath);
          const treeTab: EditorTab = {
            path: treeTabPath, label: `${base} tree`, content: "", isDirty: false, treeData: result.tree!,
          };
          if (idx >= 0) { const n = [...prev]; n[idx] = treeTab; return n; }
          return [...prev, treeTab];
        });
      }

      if (result.symbolTable) {
        const symbolsTabPath = `${inputPath}::symbols`;
        placeResult(symbolsTabPath);
        setTabs((prev) => {
          const idx = prev.findIndex((t) => t.path === symbolsTabPath);
          const symbolsTab: EditorTab = {
            path: symbolsTabPath, label: `${base} symbols`, content: "", isDirty: false, symbolTableData: result.symbolTable!,
          };
          if (idx >= 0) { const n = [...prev]; n[idx] = symbolsTab; return n; }
          return [...prev, symbolsTab];
        });
      }
 
      const tacTabPath = `${inputPath}::tac`;
      const savedTacPath = `output/${base}/${fileName}.tac`;

      if (result.errors.length > 0 || result.tac === null) {
        const count = result.errors.length;
        const reason = count > 0
          ? `${count} ${count === 1 ? "error" : "errores"}`
          : "el compilador no devolvió TAC";

        setTacNotice(
          `${inputPath}: no se generó código intermedio (${reason}).`
        );

        setTabs((prev) => prev.filter(
          (tab) => tab.path !== tacTabPath && tab.path !== savedTacPath
        ));
        activate(inputPath, sourcePane);
      } else {
        setTacNotice(null);

        const tacTab: EditorTab = {
          path: tacTabPath,
          label: `${base} tac`,
          content: "",
          isDirty: false,
          tacData: {
            lines: result.tac,
            stats: result.tacStats,
            errorCount: 0,
          },
        };

        placeResult(tacTabPath);
        setTabs((prev) => {
          // Retira una vista del archivo guardado que podría estar vieja.
          const updated = prev.filter((tab) => tab.path !== savedTacPath);
          const index = updated.findIndex((tab) => tab.path === tacTabPath);
          if (index >= 0) {
            updated[index] = tacTab;
            return updated;
          }
          return [...updated, tacTab];
        });
        // Fuente a la izquierda, TAC a la derecha; el foco queda en la fuente
        setActiveByPane((prev) => (sourcePane === 0 ? [inputPath, tacTabPath] : [tacTabPath, inputPath]));
        setFocusedPane(sourcePane);
      }

      await refreshTree();
    } catch (e: any) {
      appendTerminal(`Error: ${e.message}`);
    }
  }, [tabs, appendTerminal, refreshTree, activate, paneFor]);
 
  const paneTabs = ([0, 1] as Pane[]).map((p) => tabs.filter((t) => (paneOf[t.path] ?? 0) === p));
  const visiblePanes = ([0, 1] as Pane[]).filter((p) => paneTabs[p].length > 0);
  if (visiblePanes.length === 0) visiblePanes.push(0);
  const split = visiblePanes.length === 2;
  const focus: Pane = visiblePanes.includes(focusedPane) ? focusedPane : visiblePanes[0];
  const activeTab = activeByPane[focus];

  const activeTabData = tabs.find((t) => t.path === activeTab) ?? null;
  const canRun = (pane: Pane) => {
    const path = activeByPane[pane];
    const tab = tabs.find((t) => t.path === path);
    return !!path && path.endsWith(".cps") && !tab?.treeData && !tab?.symbolTableData && !tab?.tacData;
  };
 
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
        {tacNotice && (
          <div className="compile-notice" role="alert">
            {tacNotice}
          </div>
        )}
        <div className="editor-area" ref={editorAreaRef}>
          {visiblePanes.map((pane, index) => (
            <Fragment key={pane}>
              {index > 0 && <div className="split-handle" onMouseDown={onSplitStart} />}
              <EditorPane
                tabs={paneTabs[pane]}
                activeTab={activeByPane[pane]}
                focused={pane === focus}
                canMove={tabs.length > 1 || split}
                moveLabel={split ? "⇄ Mover al otro panel" : "◫ Dividir"}
                style={split && index === 0 ? { flex: `0 0 ${splitRatio * 100}%` } : undefined}
                onFocus={() => setFocusedPane(pane)}
                onSelectTab={(path) => activate(path, pane)}
                onCloseTab={closeTab}
                onMoveTab={moveTab}
                onChangeContent={updateTabContent}
                onSave={saveTab}
                onRunFile={canRun(pane) ? runFile : undefined}
                location={editorLocation}
              />
            </Fragment>
          ))}
        </div>
        <div className="resize-handle" onMouseDown={onResizeStart} />
        <TerminalPane
          lines={terminalLines}
          onClear={() => {
            setTerminalLines([]);
            setDiagnostics([]);
          }}
          height={terminalHeight}
          diagnostics={diagnostics}
          onGoToDiagnostic={goToDiagnostic}
        />
      </div>
 
      <StatusBar
        activeFile={activeTabData?.path ?? null}
        isDirty={activeTabData?.isDirty ?? false}
      />
    </div>
  );
}
