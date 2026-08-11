import { useState, useCallback } from "react";
import type { FileNode } from "../../types";
import { api } from "../../api";
import "./FileExplorer.css";

interface Props {
  tree: FileNode[];
  activeFile: string | null;
  onOpenFile: (node: FileNode) => void;
  onRefresh: () => void;
  appendTerminal: (line: string) => void;
  refreshTree: () => void;
}

export default function FileExplorer({ tree, activeFile, onOpenFile, onRefresh, appendTerminal }: Props) {
  // createTarget is the folder path prefix for new file creation, or "" for root.
  const [createTarget, setCreateTarget] = useState<string | null>(null);
  const [newName, setNewName] = useState("");

  const startCreate = useCallback((folderPath: string) => {
    setCreateTarget(folderPath);
    setNewName("");
  }, []);

  const handleCreate = useCallback(async () => {
    const name = newName.trim();
    if (!name || createTarget === null) { setCreateTarget(null); return; }
    // If createTarget is non-empty (a folder), prepend it.
    const fullPath = createTarget ? `${createTarget}/${name}` : name;
    try {
      await api.createFile(fullPath);
      onRefresh();
    } catch (e: any) {
      appendTerminal(`Error: ${e.message}`);
    } finally {
      setCreateTarget(null);
      setNewName("");
    }
  }, [createTarget, newName, onRefresh, appendTerminal]);

  const handleDelete = useCallback(async (node: FileNode, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm(`Delete "${node.name}"?`)) return;
    try {
      await api.deleteFile(node.path);
      onRefresh();
    } catch (e: any) {
      appendTerminal(`Error: ${e.message}`);
    }
  }, [onRefresh, appendTerminal]);

  return (
    <div className="file-explorer">
      <div className="file-explorer__header">
        <span className="panel-title">Explorer</span>
        <div className="file-explorer__toolbar">
          <button title="New File at root" onClick={() => startCreate("")}>＋</button>
          <button title="Refresh" onClick={onRefresh}>↻</button>
        </div>
      </div>

      {createTarget !== null && (
        <div className="file-explorer__create-row">
          <span className="create-icon">📄</span>
          {createTarget && <span className="create-prefix">{createTarget}/</span>}
          <input
            autoFocus
            className="file-explorer__input"
            placeholder="filename"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter")  handleCreate();
              if (e.key === "Escape") { setCreateTarget(null); setNewName(""); }
            }}
          />
        </div>
      )}

      <div className="file-explorer__tree">
        {tree.length === 0 ? (
          <div className="file-explorer__empty">
            <p>Workspace is empty.</p>
          </div>
        ) : (
          tree.map((n) => (
            <TreeNode
              key={n.path}
              node={n}
              depth={0}
              activeFile={activeFile}
              onOpen={onOpenFile}
              onDelete={handleDelete}
              onCreateIn={startCreate}
            />
          ))
        )}
      </div>
    </div>
  );
}

interface NodeProps {
  node: FileNode;
  depth: number;
  activeFile: string | null;
  onOpen: (n: FileNode) => void;
  onDelete: (n: FileNode, e: React.MouseEvent) => void;
  onCreateIn: (folderPath: string) => void;
}

function TreeNode({ node, depth, activeFile, onOpen, onDelete, onCreateIn }: NodeProps) {
  const [open, setOpen] = useState(true);
  const isActive = !node.isDir && node.path === activeFile;

  return (
    <>
      <div
        className={`tree-node ${isActive ? "active" : ""}`}
        style={{ paddingLeft: `${10 + depth * 14}px` }}
        onClick={() => node.isDir ? setOpen((v) => !v) : onOpen(node)}
      >
        <span className="tree-node__caret">
          {node.isDir ? (open ? "▾" : "▸") : ""}
        </span>
        <span className="tree-node__icon">{fileIcon(node)}</span>
        <span className="tree-node__name">{displayName(node)}</span>

        <div className="tree-node__actions">
          {node.isDir && (
            <button
              className="tree-node__action"
              title={`New file in ${node.name}/`}
              onClick={(e) => { e.stopPropagation(); onCreateIn(node.path); }}
            >＋</button>
          )}
          <button
            className="tree-node__del"
            title="Delete"
            onClick={(e) => onDelete(node, e)}
          >×</button>
        </div>
      </div>
      {node.isDir && open && node.children?.map((c) => (
        <TreeNode
          key={c.path}
          node={c}
          depth={depth + 1}
          activeFile={activeFile}
          onOpen={onOpen}
          onDelete={onDelete}
          onCreateIn={onCreateIn}
        />
      ))}
    </>
  );
}

function displayName(node: FileNode): string {
  return node.name;
}

function fileIcon(node: FileNode): string {
  if (node.isDir) return "📁";
  if (node.name.endsWith(".cps"))  return "⚙";
  if (node.name.endsWith(".out"))  return "📋";
  if (node.name.endsWith(".tree")) return "🌳";
  if (node.name.endsWith(".json")) return "{}";
  return "📄";
}
