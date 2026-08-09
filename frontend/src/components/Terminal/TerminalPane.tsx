import { useEffect, useRef } from "react";
import "./Terminal.css";

interface Props {
  lines: string[];
  onClear: () => void;
  height: number;
}

export default function TerminalPane({ lines, onClear, height }: Props) {
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
