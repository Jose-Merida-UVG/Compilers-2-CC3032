import { useState } from "react";
import type { ParseTreeNode } from "../../types";
import "./ParseTreeViewer.css";

interface Props {
  data: ParseTreeNode;
}

export default function ParseTreeViewer({ data }: Props) {
  return (
    <div className="parse-tree-viewer">
      <div className="parse-tree-viewer__header">
        <span className="panel-title" style={{ padding: 0 }}>Parse Tree</span>
      </div>
      <div className="parse-tree-viewer__body">
        <TreeNode node={data} depth={0} />
      </div>
    </div>
  );
}

function TreeNode({ node, depth }: { node: ParseTreeNode; depth: number }) {
  const [open, setOpen] = useState(depth < 3);
  const hasChildren = node.children.length > 0;

  if (node.isTerminal) {
    return (
      <div className="pt-node pt-node--leaf" style={{ paddingLeft: `${depth * 16}px` }}>
        <span className="pt-node__caret" />
        <span className="pt-node__leaf-text">{node.label}</span>
      </div>
    );
  }

  return (
    <>
      <div
        className="pt-node"
        style={{ paddingLeft: `${depth * 16}px` }}
        onClick={hasChildren ? () => setOpen((v) => !v) : undefined}
      >
        <span className="pt-node__caret">{hasChildren ? (open ? "▾" : "▸") : ""}</span>
        <span className="pt-node__rule">{node.label}</span>
        {!hasChildren && <span className="pt-node__empty"> ε</span>}
      </div>
      {hasChildren && open && node.children.map((c, i) => (
        <TreeNode key={i} node={c} depth={depth + 1} />
      ))}
    </>
  );
}
