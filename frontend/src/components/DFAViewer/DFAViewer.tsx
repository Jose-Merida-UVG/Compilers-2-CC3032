import { useState, useEffect, useRef } from "react";
import type { DFAGraphData } from "../../types";
import "./DFAViewer.css";

// ── Graphviz lazy loader ──────────────────────────────────────────────────────
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let gvCache: Promise<any> | null = null;
function loadGV() {
  if (!gvCache)
    gvCache = import("@hpcc-js/wasm-graphviz").then((m) => m.Graphviz.load());
  return gvCache;
}

// ── Label helpers ─────────────────────────────────────────────────────────────

function esc(c: string) {
  if (c === "\n") return "\\n";
  if (c === "\t") return "\\t";
  if (c === "\r") return "\\r";
  if (c === " ")  return "' '";
  return c;
}

function dotEsc(s: string) {
  return s.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
}

// Only letters, digits, and unambiguous symbols (0x21–0x7E, excluding space)
// should be used as range endpoints. Space and control chars are never collapsed.
function isRangeable(c: string): boolean {
  const cp = c.codePointAt(0) ?? 0;
  return cp > 0x20 && cp <= 0x7E;
}

// Build consecutive ranges from a sorted list of individual chars.
// e.g. ["0","1","2",...,"9"] → ["0-9"]
// Space and control chars are never used as range endpoints.
function buildRanges(chars: string[]): string[] {
  if (chars.length === 0) return [];
  const sorted = [...chars].sort((a, b) => (a.codePointAt(0) ?? 0) - (b.codePointAt(0) ?? 0));
  const ranges: string[] = [];
  let rs = sorted[0], re = sorted[0];
  for (let i = 1; i < sorted.length; i++) {
    const p = sorted[i - 1], c = sorted[i];
    const consecutive =
      p.length === 1 && c.length === 1 &&
      isRangeable(p) && isRangeable(c) &&
      c.codePointAt(0)! === p.codePointAt(0)! + 1;
    if (consecutive) {
      re = c;
    } else {
      ranges.push(rs === re ? esc(rs) : `${esc(rs)}-${esc(re)}`);
      rs = re = c;
    }
  }
  ranges.push(rs === re ? esc(rs) : `${esc(rs)}-${esc(re)}`);
  return ranges;
}

// Short label shown on edge: collapse to ranges, truncate if too many.
function shortLabel(chars: string[]): string {
  const r = buildRanges(chars);
  if (r.length <= 3) return r.join(" ");
  return `${r.slice(0, 3).join(" ")} +${r.length - 3}`;
}

// Full label shown in tooltip.
function fullLabel(chars: string[]): string {
  return buildRanges(chars).join("  ");
}

// ── DOT generation ────────────────────────────────────────────────────────────

function toDot(data: DFAGraphData): { dot: string; edgeTitles: Map<string, string> } {
  // Stable short names: start state = q0, then ascending by ID.
  const sorted = [...data.nodes].sort((a, b) =>
    a.start ? -1 : b.start ? 1 : parseInt(a.id) - parseInt(b.id)
  );
  const nameOf = new Map(sorted.map((n, i) => [n.id, `q${i}`]));

  // Merge any residual parallel edges (shouldn't happen post-SerializeDFA but be safe).
  const groups = new Map<string, string[]>();
  for (const e of data.edges) {
    const k = `${e.source}||${e.target}`;
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k)!.push(...e.symbols);
  }

  const lines: string[] = [];
  lines.push("digraph DFA {");
  lines.push("  rankdir=LR");
  lines.push('  graph [bgcolor="transparent" pad="0.5" nodesep="0.8" ranksep="1.2"]');
  lines.push('  node [shape=circle fontname="Courier New" fontsize=11 width=0.7 fixedsize=true style=filled]');
  lines.push('  edge [fontname="Courier New" fontsize=9 labeldistance=1.2 labelangle=20]');
  lines.push("");
  lines.push('  __start [shape=point width=0 style=invis label=""]');

  const startNode = data.nodes.find((n) => n.start);
  if (startNode)
    lines.push(`  __start -> "${nameOf.get(startNode.id)}" [color="#7070a0" arrowsize=0.8]`);
  lines.push("");

  // Nodes — show qN and token ID (tN) for accept states.
  for (const n of data.nodes) {
    const name = nameOf.get(n.id)!;
    const tokenMatch = n.accept ? n.label.match(/\/t(\d+)$/) : null;
    const tokenTag   = tokenMatch ? `/t${tokenMatch[1]}` : "";
    // Display: two lines — qN on top, small /tN below for accept states only.
    const dispLabel  = tokenTag ? `${name}\\n${tokenTag}` : name;

    const attrs: string[] = [`label="${dispLabel}"`];

    if (n.accept) {
      attrs.push("shape=doublecircle", 'fillcolor="#0c1e16"', 'color="#0db880"', 'fontcolor="#6ee7b7"');
    } else {
      attrs.push('fillcolor="#1a1a2c"', 'color="#505075"', 'fontcolor="#8888b0"');
    }
    if (n.start) {
      attrs.push('color="#7b4fd8"', 'fontcolor="#c4b5fd"');
      if (!n.accept) attrs.push('fillcolor="#160d2e"');
    }
    attrs.push(`tooltip="${dotEsc(n.label)}"`);
    lines.push(`  "${name}" [${attrs.join(" ")}]`);
  }
  lines.push("");

  // Edges — build a title map so we can replace Graphviz's default "q0->q1" titles.
  const edgeTitles = new Map<string, string>();
  for (const [k, chars] of groups) {
    const [src, tgt] = k.split("||");
    const s  = nameOf.get(src)!, t = nameOf.get(tgt)!;
    const sl = dotEsc(shortLabel(chars));
    const fl = fullLabel(chars);
    edgeTitles.set(`${s}->${t}`, fl);
    lines.push(`  "${s}" -> "${t}" [label="${sl}" tooltip="${dotEsc(fl)}" color="#555575" fontcolor="#a090cc"]`);
  }

  lines.push("}");
  return { dot: lines.join("\n"), edgeTitles };
}

// ── Component ─────────────────────────────────────────────────────────────────

interface Props { data: DFAGraphData | null; }

export default function DFAViewer({ data }: Props) {
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

  // Non-passive wheel for zoom toward cursor.
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const k    = e.deltaY < 0 ? 1.12 : 0.89;
      const rect = el.getBoundingClientRect();
      const mx   = e.clientX - rect.left, my = e.clientY - rect.top;
      const { tx, ty, scale } = tf.current;
      const ns = Math.max(0.08, Math.min(8, scale * k));
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

  // After SVG renders, widen the invisible hit area on edges so hover tooltips work.
  useEffect(() => {
    if (!svg || !innerRef.current) return;
    const svgEl = innerRef.current.querySelector("svg");
    if (!svgEl) return;
    svgEl.querySelectorAll("g.edge").forEach((g) => {
      g.querySelectorAll("path").forEach((path) => {
        const hit = path.cloneNode() as SVGPathElement;
        hit.style.strokeWidth = "14px";
        hit.style.stroke      = "rgba(0,0,0,0.01)";
        hit.style.fill        = "none";
        hit.style.cursor      = "crosshair";
        g.appendChild(hit);
      });
    });
  }, [svg]);

  useEffect(() => {
    if (!data) { setSvg(null); setStatus("idle"); return; }
    setStatus("loading"); setSvg(null);
    const { dot, edgeTitles } = toDot(data);
    loadGV()
      .then((gv) => {
        let raw: string = gv.dot(dot);
        // Strip XML declaration + DOCTYPE — not valid inside a div.
        // Also strip <a> wrappers Graphviz injects for tooltip/href — they cause a
        // hand cursor and break native <title> tooltips (xlink:title is deprecated).
        raw = raw
          .replace(/<\?xml[^?]*\?>\s*/g, "")
          .replace(/<!DOCTYPE[^>]*>\s*/g, "");
        // Before stripping <a> wrappers, rescue xlink:title values that Graphviz puts tooltip
        // content into — move them onto the sibling <title> element inside the same <g>.
        // Pattern: <g class="edge">...<title>q0->q1</title>...<a xlink:title="LABEL">
        raw = raw.replace(
          /(<g[^>]*class="edge"[^>]*>[\s\S]*?<title>)([\s\S]*?)(<\/title>[\s\S]*?)<a\s[^>]*xlink:title="([^"]*)"[^>]*>/g,
          (_m, open, _oldTitle, mid, xlinkTitle) => `${open}${xlinkTitle}${mid}`
        );
        raw = raw.replace(/<a\s[^>]*>/g, "").replace(/<\/a>/g, "");
        // Fallback: replace any remaining "q0->q1" style titles using our edgeTitles map.
        edgeTitles.forEach((label, key) => {
          const encodedLabel = label.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
          // Try both raw '>' and encoded '&gt;' since Graphviz may or may not encode it.
          for (const k of [key, key.replace(/>/g, "&gt;")]) {
            const escaped = k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
            raw = raw.replace(new RegExp(`<title>${escaped}<\\/title>`), `<title>${encodedLabel}</title>`);
          }
        });
        const out = raw;
        setSvg(out);
        setStatus("idle");
        tf.current = { tx: 20, ty: 20, scale: 1 };
        applyTf();
      })
      .catch((err: unknown) => { setStatus("error"); setErrMsg(String(err)); });
  }, [data]);

  if (!data) return (
    <div className="dfa-viewer dfa-viewer--empty">
      <div className="panel-title">DFA Viewer</div>
      <p className="dfa-viewer__hint">Open a <code>.yal</code> spec and click <strong>◎ Build</strong> to visualize the automaton.</p>
    </div>
  );

  return (
    <div className="dfa-viewer">
      <div className="dfa-viewer__stats">
        <span>{data.nodes.length} states</span>
        <span className="dfa-viewer__sep">·</span>
        <span>{new Set(data.edges.map((e) => `${e.source}||${e.target}`)).size} transitions</span>
        <span className="dfa-viewer__sep">·</span>
        <span className="dfa-viewer__legend">
          <span className="dfa-legend dfa-legend--start"  /> start&nbsp;
          <span className="dfa-legend dfa-legend--accept" /> accept
        </span>
        <span className="dfa-viewer__sep">·</span>
        <span className="dfa-viewer__hint-inline">scroll=zoom · drag=pan · hover edge=full symbols</span>
      </div>

      <div
        className="dfa-viewer__canvas"
        ref={containerRef}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
      >
        {status === "loading" && <div className="dfa-overlay">Rendering automaton…</div>}
        {status === "error"   && <div className="dfa-overlay dfa-overlay--error">Graphviz error: {errMsg}</div>}
        <div
          ref={innerRef}
          className="dfa-inner"
          dangerouslySetInnerHTML={svg ? { __html: svg } : undefined}
        />
      </div>
    </div>
  );
}
