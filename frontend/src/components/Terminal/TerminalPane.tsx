import { useEffect, useRef } from "react";
import type { CompilerDiagnostic } from "../../types";
import "./Terminal.css";

interface Props {
  lines: string[];
  onClear: () => void;
  height: number;
  diagnostics: CompilerDiagnostic[];
  onGoToDiagnostic: (diagnostic: CompilerDiagnostic) => void;
}

export default function TerminalPane({ lines, onClear, height, diagnostics, onGoToDiagnostic, }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  return (
    <div className="terminal-pane" style={{ height: `${height}px` }}>
      <div className="terminal-pane__header">
        <span className="terminal-pane__title">OUTPUT</span>
        <div className="terminal-pane__actions">
          <button title="Clear" onClick={onClear}>⊘ Clear</button>
        </div>
      </div>

      <div className="terminal-pane__body">
        {diagnostics.length > 0 && (
          <section className="diagnostics" aria-label="Errores de compilación">
            <h3 className="diagnostics__title">
              Errores de la última compilación ({diagnostics.length})
            </h3>

            {diagnostics.map((diagnostic, index) => (
              <button
                key={`${diagnostic.path}-${index}`}
                type="button"
                className="diagnostics__item"
                disabled={diagnostic.line === null || diagnostic.column === null}
                onClick={() => onGoToDiagnostic(diagnostic)}
                title="Ir al error en el código fuente"
              >
                <span className="diagnostics__file">{diagnostic.path}</span>
                <span>{diagnostic.message}</span>
              </button>
            ))}
          </section>
        )}

        {lines.map((line, i) => (
          <div key={i} className={`terminal-line ${classify(line)}`}>
            {line}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

function classify(line: string): string {
  if (line.startsWith("Error") || line.startsWith("ERROR")) return "error";
  if (line.startsWith("Saved") || line.startsWith("──")) return "success";
  if (line.startsWith("▶") || line.startsWith("Building")) return "info";
  if (line.trim().length > 0) return "match";
  return "";
}
