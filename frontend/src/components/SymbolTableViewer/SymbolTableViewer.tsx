import { useState } from "react";
import type { ScopeNode } from "../../types";
import "./SymbolTableViewer.css";

interface Props {
  data: ScopeNode;
}

export default function SymbolTableViewer({ data }: Props) {
  return (
    <div className="symbol-table-viewer">
      <div className="symbol-table-viewer__header">
        <span className="panel-title" style={{ padding: 0 }}>Tabla de símbolos</span>
      </div>
      <div className="symbol-table-viewer__body">
        <ScopeNodeView node={data} depth={0} />
      </div>
    </div>
  );
}

function scopeLabel(node: ScopeNode): string {
  const kind = node.kind.charAt(0) + node.kind.slice(1).toLowerCase();
  return node.owner ? `${kind} · ${node.owner}` : kind;
}

function ScopeNodeView({ node, depth }: { node: ScopeNode; depth: number }) {
  const [open, setOpen] = useState(depth < 2);
  const hasChildren = node.children.length > 0;
  const hasSymbols = node.symbols.length > 0;

  return (
    <>
      <div
        className="st-node"
        style={{ paddingLeft: `${depth * 16}px` }}
        onClick={() => setOpen((v) => !v)}
      >
        <span className="st-node__caret">{open ? "▾" : "▸"}</span>
        <span className={`st-node__kind st-node__kind--${node.kind.toLowerCase()}`}>
          {scopeLabel(node)}
        </span>
        {!hasSymbols && !hasChildren && <span className="st-node__empty"> vacío</span>}
      </div>
      {open && (
        <>
          {hasSymbols && (
            <table className="st-symbols" style={{ marginLeft: `${depth * 16 + 20}px` }}>
              <tbody>
                {node.symbols.map((s, i) => (
                  <tr key={i} className="st-symbols__row">
                    <td className={`st-symbols__badge st-symbols__badge--${s.kind.toLowerCase()}`}>
                      {s.kind.toLowerCase()}
                    </td>
                    <td className="st-symbols__name">{s.name}</td>
                    <td className="st-symbols__type">{s.type}</td>
                    <td className="st-symbols__loc">{s.line}:{s.column}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {node.children.map((c, i) => (
            <ScopeNodeView key={i} node={c} depth={depth + 1} />
          ))}
        </>
      )}
    </>
  );
}
