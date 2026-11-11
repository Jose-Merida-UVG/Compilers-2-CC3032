import { useState } from "react";
import type { ActivationData, ActivationFrame, ActivationSlot, ActivationTreeNode } from "../../types";
import "./ActivationViewer.css";

interface Props {
  data: ActivationData;
}

/** El backend manda `{}` mientras no existe el generador de activación: eso no se dibuja. */
export function isValidActivation(a: unknown): a is ActivationData {
  const data = a as Partial<ActivationData> | null | undefined;
  return !!data && typeof data.frames === "object" && data.frames !== null
    && Object.keys(data.frames).length > 0 && !!data.tree && typeof data.tree.label === "string";
}

/** Árbol de activación (quién llama a quién) y registro de activación (pila) de cada función. */
export default function ActivationViewer({ data }: Props) {
  const labels = Object.keys(data.frames);
  const first = data.tree.children.find((c) => data.frames[c.label])?.label;
  const [selected, setSelected] = useState<string>(first ?? data.tree.label);

  return (
    <div className="act-viewer">
      <div className="act-viewer__header">
        <span className="panel-title" style={{ padding: 0 }}>Registros y árbol de activación</span>
      </div>
      <div className="act-viewer__body">
        <section className="act-panel act-panel--tree" aria-label="Árbol de activación">
          <h3 className="act-panel__title">Árbol de activación</h3>
          <div className="act-legend">
            <span><b className="act-mark act-mark--rec">↻</b> recursiva</span>
            <span><b className="act-mark act-mark--cut">…</b> recursión truncada</span>
            <span><b className="act-mark act-mark--virt">virtual</b> llamada dinámica</span>
          </div>
          <div className="act-tree">
            <TreeNode node={data.tree} depth={0} selected={selected} onSelect={setSelected} frames={data.frames} />
          </div>
        </section>

        <section className="act-panel act-panel--frame" aria-label="Registro de activación">
          <div className="act-panel__head">
            <h3 className="act-panel__title">Registro de activación</h3>
            <select
              className="act-select"
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
              aria-label="Función"
            >
              {!data.frames[selected] && <option value={selected}>{selected}</option>}
              {labels.map((l) => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>
          {data.frames[selected]
            ? <FrameStack frame={data.frames[selected]} />
            : <p className="act-empty">No hay datos de marco para «{selected}».</p>}
        </section>
      </div>
    </div>
  );
}

// ── árbol ───────────────────────────────────────────────────────────────────
function TreeNode(props: {
  node: ActivationTreeNode;
  depth: number;
  selected: string;
  onSelect: (label: string) => void;
  frames: Record<string, ActivationFrame>;
}) {
  const { node, depth, selected, onSelect, frames } = props;
  const [open, setOpen] = useState(depth < 3);
  const hasChildren = node.children.length > 0;
  const known = !!frames[node.label];

  return (
    <>
      <div
        className={`act-node ${node.label === selected ? "act-node--selected" : ""}`}
        style={{ paddingLeft: `${depth * 16}px` }}
        onClick={() => known && onSelect(node.label)}
        title={known ? "Ver el registro de activación" : undefined}
      >
        <button
          type="button"
          className="act-node__caret"
          aria-label={open ? "Colapsar" : "Expandir"}
          disabled={!hasChildren}
          onClick={(e) => { e.stopPropagation(); setOpen((v) => !v); }}
        >
          {hasChildren ? (open ? "▾" : "▸") : ""}
        </button>
        <span className={`act-node__label ${known ? "" : "act-node__label--unknown"}`}>{node.label}</span>
        {node.recursive && <b className="act-mark act-mark--rec" title="llamada recursiva">↻</b>}
        {node.truncated && <b className="act-mark act-mark--cut" title="se cortó el despliegue de la recursión">…</b>}
        {node.virtual && <b className="act-mark act-mark--virt" title="llamada virtual (resuelta por tipo estático)">virtual</b>}
        {node.line && <span className="act-node__line">{node.line}</span>}
      </div>
      {open && node.children.map((c, i) => (
        <TreeNode key={i} node={c} depth={depth + 1} selected={selected} onSelect={onSelect} frames={frames} />
      ))}
    </>
  );
}

// ── pila del registro de activación ────────────────────────────────────────────
const GROUPS: Record<string, string> = {
  param: "Argumentos (los empuja el llamador)",
  saved: "Registros guardados",
  local: "Variables locales",
  temp: "Temporales",
};

function FrameStack({ frame }: { frame: ActivationFrame }) {
  const counts = (kind: string) => frame.slots.filter((s) => s.kind === kind).length;
  const rows: React.ReactNode[] = [];
  let lastKind = "";

  frame.slots.forEach((slot, i) => {
    if (slot.kind !== lastKind) {
      rows.push(<div key={`g${i}`} className="act-group">{GROUPS[slot.kind] ?? slot.kind}</div>);
      lastKind = slot.kind;
    }
    rows.push(<SlotRow key={i} slot={slot} />);
  });

  return (
    <div className="act-frame">
      <div className="act-frame__chips">
        <span className="act-chip">{frame.total_size} B en total</span>
        <span className="act-chip">{plural(counts("param"), "parámetro", "parámetros")}</span>
        <span className="act-chip">{plural(counts("local"), "local", "locales")}</span>
        <span className="act-chip">{plural(counts("temp"), "temporal", "temporales")}</span>
      </div>
      <div className="act-stack" role="list">
        <div className="act-axis act-axis--top">↑ direcciones altas</div>
        {rows}
        <div className="act-sp"><span>$sp</span> →</div>
        <div className="act-axis act-axis--bottom">↓ direcciones bajas · la pila crece hacia abajo</div>
      </div>
    </div>
  );
}

function plural(n: number, one: string, many: string): string {
  return `${n} ${n === 1 ? one : many}`;
}

function SlotRow({ slot }: { slot: ActivationSlot }) {
  const isFp = slot.name === "$fp";
  return (
    <div className={`act-slot act-slot--${slot.kind}`} role="listitem">
      <span className="act-slot__addr">{slot.address}</span>
      <span className="act-slot__box">
        <span className="act-slot__name">{slot.name}</span>
        <span className="act-slot__kind">{slot.kind === "saved" ? "guardado" : slot.kind}</span>
      </span>
      <span className="act-slot__size">{slot.size} B</span>
      {isFp && <span className="act-slot__ptr">◄ $fp</span>}
    </div>
  );
}
