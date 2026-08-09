import { useState, useEffect, useRef } from "react";
import type { LR0GraphData } from "../../types";
import "./LR0Viewer.css";

// ── Graphviz lazy loader ──────────────────────────────────────────────────────
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let gvCache: Promise<any> | null = null;
function loadGV() {
  if (!gvCache)
    gvCache = import("@hpcc-js/wasm-graphviz").then((m) => m.Graphviz.load());
  return gvCache;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function htmlEsc(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}


// ── DOT generation ────────────────────────────────────────────────────────────

function toDot(data: LR0GraphData): string {
  const lines: string[] = [];

  lines.push("digraph LR0 {");
  lines.push("  rankdir=LR");
  lines.push('  graph [bgcolor="transparent" pad="0.5" nodesep="0.4" ranksep="0.8" splines=ortho]');
  lines.push('  edge [fontname="Courier New" fontsize=10 color="#555575" fontcolor="#a090cc" arrowsize=0.7]');
  lines.push('  node [shape=none fontname="Courier New" fontsize=10]');
  lines.push("");

  lines.push('  __start [shape=point width=0 style=invis label=""]');
  lines.push('  __start -> "0" [color="#7b4fd8" arrowsize=0.8]');
  lines.push("");

  for (const node of data.nodes) {
    const headerBg  = node.isStart  ? "#1e0f40" : node.isAccept ? "#0c1e16" : "#1a1a2c";
    const headerFg  = node.isStart  ? "#c4b5fd" : node.isAccept ? "#6ee7b7" : "#8888b0";
    const borderCol = node.isStart  ? "#7b4fd8" : node.isAccept ? "#0db880" : "#505075";

    const itemRows = node.items.map((item) =>
      `<TR><TD ALIGN="LEFT" BALIGN="LEFT" BGCOLOR="#12121e"><FONT COLOR="#c8c8d8">${htmlEsc(item)}</FONT></TD></TR>`
    ).join("\n        ");

    const label = `<
      <TABLE BORDER="2" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" COLOR="${borderCol}">
        <TR><TD BGCOLOR="${headerBg}"><FONT COLOR="${headerFg}"><B>${htmlEsc(node.label)}</B></FONT></TD></TR>
        <HR/>
        ${itemRows}
      </TABLE>>`;

    lines.push(`  "${node.id}" [label=${label}]`);
  }

  lines.push("");

  for (const edge of data.edges) {
    lines.push(`  "${edge.source}" -> "${edge.target}" [taillabel="${htmlEsc(edge.symbol)}" labeldistance=2.0 labelangle=15]`);
  }

  lines.push("}");
  return lines.join("\n");
}

// ── Component ─────────────────────────────────────────────────────────────────

interface Props { data: LR0GraphData | null; }

export default function LR0Viewer({ data }: Props) {
  const [svg, setSvg]       = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [errMsg, setErrMsg] = useState("");

  const containerRef = useRef<HTMLDivElement>(null);
  const innerRef     = useRef<HTMLDivElement>(null);
  const tf   = useRef({ tx: 20, ty: 20, scale: 1 });
  const drag = useRef({ on: false, sx: 0, sy: 0, stx: 0, sty: 0 });

  function applyTf() {
    if (innerRef.current) {
      const { tx, ty, scale } = tf.current;
      innerRef.current.style.transform = `translate(${tx}px,${ty}px) scale(${scale})`;
    }
  }

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const k    = e.deltaY < 0 ? 1.12 : 0.89;
      const rect = el.getBoundingClientRect();
      const mx   = e.clientX - rect.left, my = e.clientY - rect.top;
      const { tx, ty, scale } = tf.current;
      const ns = Math.max(0.05, Math.min(8, scale * k));
      tf.current = {
        tx: mx - (mx - tx) * (ns / scale),
        ty: my - (my - ty) * (ns / scale),
        scale: ns,
      };
      applyTf();
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, []);

  const onMouseDown = (e: React.MouseEvent) => {
    drag.current = { on: true, sx: e.clientX, sy: e.clientY, stx: tf.current.tx, sty: tf.current.ty };
  };
  const onMouseMove = (e: React.MouseEvent) => {
    if (!drag.current.on) return;
    tf.current.tx = drag.current.stx + e.clientX - drag.current.sx;
    tf.current.ty = drag.current.sty + e.clientY - drag.current.sy;
    applyTf();
  };
  const onMouseUp = () => { drag.current.on = false; };


  useEffect(() => {
    if (!data) { setSvg(null); setStatus("idle"); return; }
    setStatus("loading"); setSvg(null);

    const dot = toDot(data);
    loadGV()
      .then((gv) => {
        let raw: string = gv.dot(dot);
        raw = raw
          .replace(/<\?xml[^?]*\?>\s*/g, "")
          .replace(/<!DOCTYPE[^>]*>\s*/g, "");
        setSvg(raw);
        setStatus("idle");
        tf.current = { tx: 20, ty: 20, scale: 1 };
        applyTf();
      })
      .catch((err: unknown) => { setStatus("error"); setErrMsg(String(err)); });
  }, [data]);

  if (!data) return (
    <div className="lr0-viewer lr0-viewer--empty">
      <div className="panel-title">LR(0) Viewer</div>
      <p className="lr0-viewer__hint">Open a <code>.yalp</code> spec and click <strong>◎ Build Parser</strong> to visualize the automaton.</p>
    </div>
  );

  const stateCount      = data.nodes.length;
  const transitionCount = data.edges.length;
  const acceptCount     = data.nodes.filter((n) => n.isAccept).length;

  return (
    <div className="lr0-viewer">
      <div className="lr0-viewer__stats">
        <span>{stateCount} states</span>
        <span className="lr0-viewer__sep">·</span>
        <span>{transitionCount} transitions</span>
        <span className="lr0-viewer__sep">·</span>
        <span>{acceptCount} accept</span>
        <span className="lr0-viewer__sep">·</span>
        <span className="lr0-viewer__legend">
          <span className="lr0-legend lr0-legend--start"  /> start&nbsp;
          <span className="lr0-legend lr0-legend--accept" /> accept
        </span>
        <span className="lr0-viewer__sep">·</span>
        <span className="lr0-viewer__hint-inline">scroll=zoom · drag=pan</span>
      </div>

      <div
        className="lr0-viewer__canvas"
        ref={containerRef}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
      >
        {status === "loading" && <div className="lr0-overlay">Rendering automaton…</div>}
        {status === "error"   && <div className="lr0-overlay lr0-overlay--error">Graphviz error: {errMsg}</div>}
        <div
          ref={innerRef}
          className="lr0-inner"
          dangerouslySetInnerHTML={svg ? { __html: svg } : undefined}
        />
      </div>
    </div>
  );
}
