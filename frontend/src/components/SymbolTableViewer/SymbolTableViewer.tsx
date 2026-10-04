import { useState } from "react";
import type { ClassLayout, FrameInfo, ScopeNode, SymbolEntry } from "../../types";
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

/** Variables, constantes y parámetros que el TAC renombra por sombreado. */
function isRenamed(s: SymbolEntry): boolean {
  const data = s.kind === "VARIABLE" || s.kind === "CONSTANT" || s.kind === "PARAMETER";
  return data && s.tac_name !== null && s.tac_name !== s.name;
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
          {node.frame && <FrameView frame={node.frame} indent={depth * 16 + 20} />}
          {node.layout && <LayoutView layout={node.layout} indent={depth * 16 + 20} />}
          {hasSymbols && (
            <table className="st-symbols" style={{ marginLeft: `${depth * 16 + 20}px` }}>
              <tbody>
                {node.symbols.map((s, i) => (
                  <tr key={i} className="st-symbols__row">
                    <td className={`st-symbols__badge st-symbols__badge--${s.kind.toLowerCase()}`}>
                      {s.kind.toLowerCase()}
                    </td>
                    <td className="st-symbols__name">
                      {s.name}
                      {isRenamed(s) && <span className="st-symbols__tac" title="nombre en el TAC"> → {s.tac_name}</span>}
                    </td>
                    <td className="st-symbols__type">{s.type}</td>
                    <td className="st-symbols__mem" title="tamaño en bytes">
                      {s.size !== null ? `${s.size} B` : ""}
                    </td>
                    <td className="st-symbols__mem" title="dirección (gp global, fp pila, this campo)">
                      {s.address ?? ""}
                    </td>
                    <td className="st-symbols__label" title="etiqueta">{s.label ?? ""}</td>
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

/** Registro de activación: cada sección del frame en bytes. */
function FrameView({ frame, indent }: { frame: FrameInfo; indent: number }) {
  const parts: [string, number][] = [
    ["params", frame.params_size],
    ["locals", frame.locals_size],
    [`temps (${frame.temps})`, frame.temps_size],
    ["saved ra+fp", frame.saved_size],
  ];
  return (
    <div className="st-frame" style={{ marginLeft: `${indent}px` }}>
      <span className="st-frame__title">frame {frame.label}</span>
      {parts.map(([name, size]) => (
        <span key={name} className="st-chip">{name}: {size} B</span>
      ))}
      <span className="st-chip st-chip--total">total: {frame.total_size} B</span>
    </div>
  );
}

/** Layout de una clase: campos (con su offset) y métodos. */
function LayoutView({ layout, indent }: { layout: ClassLayout; indent: number }) {
  return (
    <div className="st-layout" style={{ marginLeft: `${indent}px` }}>
      <div className="st-frame">
        <span className="st-frame__title">objeto: {layout.size} B</span>
        {layout.parent && <span className="st-chip">hereda de {layout.parent}</span>}
      </div>
      {layout.fields.length > 0 && (
        <table className="st-symbols">
          <tbody>
            {layout.fields.map((f) => (
              <tr key={f.name} className="st-symbols__row">
                <td className="st-symbols__badge">campo</td>
                <td className="st-symbols__name">{f.name}</td>
                <td className="st-symbols__mem">+{f.offset}</td>
                <td className="st-symbols__mem">{f.size} B</td>
                <td className="st-symbols__type">{f.inherited ? "heredado" : ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {layout.methods.length > 0 && (
        <table className="st-symbols">
          <tbody>
            {layout.methods.map((m) => (
              <tr key={m.label} className="st-symbols__row">
                <td className="st-symbols__badge st-symbols__badge--function">método</td>
                <td className="st-symbols__name">{m.name}</td>
                <td className="st-symbols__label">{m.label}</td>
                <td className="st-symbols__type">{m.overrides ? `sobrescribe ${m.overrides}` : ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
