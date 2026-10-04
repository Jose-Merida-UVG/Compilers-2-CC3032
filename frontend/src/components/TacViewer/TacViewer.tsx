import type { TacData } from "../../types";
import "./TacViewer.css";

interface Props {
  data: TacData;
}

export default function TacViewer({ data }: Props) {
  const { lines, stats, errorCount } = data;

  if (lines === null) {
    const noun = errorCount === 1 ? "error" : "errores";
    return (
      <div className="tac-viewer">
        <div className="tac-viewer__header">
          <span className="panel-title" style={{ padding: 0 }}>Código intermedio (TAC)</span>
        </div>
        <div className="tac-notice">
          <div className="tac-notice__title">No se generó código intermedio</div>
          <p>
            El programa tiene {errorCount} {noun}; el TAC solo se genera cuando el análisis
            léxico, sintáctico y semántico no reporta ninguno. Corrige los errores del panel
            OUTPUT y vuelve a ejecutar.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="tac-viewer">
      <div className="tac-viewer__header">
        <span className="panel-title" style={{ padding: 0 }}>Código intermedio (TAC)</span>
        {stats && (
          <div className="tac-stats">
            <span className="tac-stats__chip">{stats.instructions} instrucciones</span>
            <span className="tac-stats__chip">{stats.functions} funciones</span>
            <span className="tac-stats__chip">{stats.temps} temporales (pico)</span>
          </div>
        )}
      </div>
      <div className="tac-viewer__body">
        {lines.map((line, i) => (
          <div key={i} className={`tac-line ${lineClass(line)}`}>
            <span className="tac-line__num">{i + 1}</span>
            <span className="tac-line__text">{renderLine(line)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

const UNIT_HEADER = /^(func|class)\s/;
const UNIT_FOOTER = /^(endfunc|endclass)$/;
const LABEL_DEF = /^L\d+:$/;

function lineClass(line: string): string {
  if (UNIT_HEADER.test(line)) return "tac-line--unit";
  if (UNIT_FOOTER.test(line)) return "tac-line--unit-end";
  if (LABEL_DEF.test(line)) return "tac-line--label";
  return "";
}

// Las cadenas van primero para no resaltar su contenido
const TOKEN =
  /("(?:[^"\\]|\\.)*")|(\$t\d+)|\b(L\d+)\b|\b(goto|ifFalse|if|param|call|return|print|newarray|new|len|itof|try|endtry|catch)\b|(-?\b\d+(?:\.\d+)?\b)/g;

function renderLine(line: string) {
  if (UNIT_HEADER.test(line) || UNIT_FOOTER.test(line) || LABEL_DEF.test(line)) {
    return line;
  }
  const out: React.ReactNode[] = [];
  let last = 0;
  let key = 0;
  for (const m of line.matchAll(TOKEN)) {
    const start = m.index ?? 0;
    if (start > last) out.push(line.slice(last, start));
    const cls = m[1] ? "str" : m[2] ? "temp" : m[3] ? "label" : m[4] ? "kw" : "num";
    out.push(<span key={key++} className={`tac-tok tac-tok--${cls}`}>{m[0]}</span>);
    last = start + m[0].length;
  }
  if (last < line.length) out.push(line.slice(last));
  return out;
}
