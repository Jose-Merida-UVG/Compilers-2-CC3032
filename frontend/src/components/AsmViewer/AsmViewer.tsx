import { useEffect, useMemo, useState } from "react";
import type { AsmData } from "../../types";
import "./AsmViewer.css";

interface Props {
  data: AsmData;
}

/** Ensamblador MIPS (solo lectura): numeración, resaltado, mirilla y exportación. */
export default function AsmViewer({ data }: Props) {
  const { lines, raw, stats, fileName } = data;
  const canCompare = raw !== null;

  const [useRaw, setUseRaw] = useState(false);
  const [showTac, setShowTac] = useState(true);
  const [status, setStatus] = useState("");

  useEffect(() => {
    setStatus("");
    setUseRaw(false);
  }, [data]);

  const shown = useRaw && raw ? raw : lines;
  const text = useMemo(() => shown.join("\n") + "\n", [shown]);

  const copyAsm = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setStatus("Ensamblador copiado.");
    } catch {
      setStatus("No se pudo copiar. Selecciona el texto y cópialo manualmente.");
    }
  };

  const saveAsm = () => {
    const name = useRaw ? fileName.replace(/\.s$/, ".sin-mirilla.s") : fileName;
    const url = URL.createObjectURL(new Blob([text], { type: "text/plain;charset=utf-8" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = name;
    link.click();
    URL.revokeObjectURL(url);
    setStatus(`Guardado como ${name}.`);
  };

  return (
    <div className="asm-viewer">
      <div className="asm-viewer__header">
        <span className="panel-title" style={{ padding: 0 }}>Ensamblador MIPS</span>
        <div className="asm-actions">
          {canCompare && (
            <div className="asm-toggle" role="group" aria-label="Mirilla">
              <button
                type="button"
                className={`asm-toggle__btn ${useRaw ? "asm-toggle__btn--on" : ""}`}
                aria-pressed={useRaw}
                onClick={() => setUseRaw(true)}
              >
                Sin mirilla
              </button>
              <button
                type="button"
                className={`asm-toggle__btn ${useRaw ? "" : "asm-toggle__btn--on"}`}
                aria-pressed={!useRaw}
                onClick={() => setUseRaw(false)}
              >
                Con mirilla
              </button>
            </div>
          )}
          <label className="asm-check" title="Muestra la línea del TAC de la que sale cada bloque">
            <input type="checkbox" checked={showTac} onChange={(e) => setShowTac(e.target.checked)} />
            Comentarios TAC
          </label>
          <button type="button" className="asm-btn" onClick={copyAsm}>Copiar</button>
          <button type="button" className="asm-btn" onClick={saveAsm}>Guardar .s</button>
        </div>
      </div>

      {stats && <PeepholeSummary stats={stats} showingRaw={useRaw} />}

      <div className="asm-status" role="status" aria-live="polite">{status}</div>

      <div className="asm-viewer__body">
        {shown.map((line, i) =>
          !showTac && isTacComment(line) ? null : (
            <div key={i} className={`asm-line ${lineClass(line)}`}>
              <span className="asm-line__num">{i + 1}</span>
              <span className="asm-line__text">{renderLine(line)}</span>
            </div>
          ),
        )}
      </div>
    </div>
  );
}

function PeepholeSummary({ stats, showingRaw }: { stats: NonNullable<AsmData["stats"]>; showingRaw: boolean }) {
  const entries = Object.entries(stats.peephole ?? {});
  const saved = stats.instructions_raw - stats.instructions;
  return (
    <div className="asm-summary">
      <span className="asm-chip asm-chip--count">
        {stats.instructions_raw} → {stats.instructions} instrucciones
        {saved > 0 && <b> (−{saved})</b>}
      </span>
      {entries.length === 0 ? (
        <span className="asm-chip">sin transformaciones de mirilla</span>
      ) : (
        entries.map(([name, times]) => (
          <span key={name} className="asm-chip" title="transformación de la mirilla (veces aplicada)">
            {name} ×{times}
          </span>
        ))
      )}
      <span className="asm-summary__mode">
        {showingRaw ? "mostrando el código sin optimizar" : "mostrando el código optimizado"}
      </span>
    </div>
  );
}

// ── resaltado ───────────────────────────────────────────────────────────────
const TAC_COMMENT = /^\s*# TAC:/;
const isTacComment = (line: string) => TAC_COMMENT.test(line);

const LABEL_DEF = /^([A-Za-z_.][\w.$]*):/;
const SECTION = /^\s*\.(data|text)\b/;
const FUNC_LABEL = /^f_[\w$]*:$/;
const RT_LABEL = /^rt_[\w$]*:$/;

function lineClass(line: string): string {
  const t = line.trim();
  if (isTacComment(line)) return "asm-line--tac";
  if (SECTION.test(line)) return "asm-line--section";
  if (FUNC_LABEL.test(t) && !t.endsWith("__ret:")) return "asm-line--func";
  if (RT_LABEL.test(t)) return "asm-line--rt";
  if (LABEL_DEF.test(t)) return "asm-line--label";
  if (t.startsWith("#")) return "asm-line--comment";
  return "";
}

// Las cadenas van primero para no resaltar su contenido
const OPERAND =
  /("(?:[^"\\]|\\.)*")|(\$[\w]+)|(-?\b\d+\.\d+\b|-?\b0x[0-9a-fA-F]+\b|-?\b\d+\b)|([A-Za-z_][\w.$]*)/g;

/** Parte la línea en código y comentario (un `#` dentro de comillas no cuenta). */
function splitComment(line: string): [string, string] {
  let inStr = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (inStr) {
      if (c === "\\") i++;
      else if (c === '"') inStr = false;
    } else if (c === '"') inStr = true;
    else if (c === "#") return [line.slice(0, i), line.slice(i)];
  }
  return [line, ""];
}

function renderLine(line: string): React.ReactNode {
  const [code, comment] = splitComment(line);
  const out: React.ReactNode[] = [];
  let key = 0;
  const push = (cls: string, text: string) =>
    out.push(<span key={key++} className={`asm-tok asm-tok--${cls}`}>{text}</span>);

  let rest = code;
  const label = LABEL_DEF.exec(rest.trimStart());
  if (label) {
    const lead = rest.length - rest.trimStart().length;
    if (lead) out.push(rest.slice(0, lead));
    push("label", label[0]);
    rest = rest.trimStart().slice(label[0].length);
  }

  const head = /^(\s*)(\.\w+|[a-z][\w.]*)/.exec(rest);
  if (head) {
    if (head[1]) out.push(head[1]);
    push(head[2].startsWith(".") ? "dir" : "ins", head[2]);
    rest = rest.slice(head[0].length);
  }

  let last = 0;
  for (const m of rest.matchAll(OPERAND)) {
    const start = m.index ?? 0;
    if (start > last) out.push(rest.slice(last, start));
    const cls = m[1] ? "str" : m[2] ? "reg" : m[3] ? "num" : "ref";
    push(cls, m[0]);
    last = start + m[0].length;
  }
  if (last < rest.length) out.push(rest.slice(last));

  if (comment) push(isTacComment(comment) ? "tac" : "comment", comment);
  return out;
}
