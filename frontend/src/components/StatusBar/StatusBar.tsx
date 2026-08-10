import "./StatusBar.css";

interface Props {
  activeFile: string | null;
  isDirty: boolean;
}

export default function StatusBar({ activeFile, isDirty }: Props) {
  const ext = activeFile?.split(".").pop() ?? null;

  return (
    <div className="status-bar">
      <span className="status-bar__left">
        <span className="status-bar__file">
          {activeFile ?? "Compiscript IDE"}
        </span>
        {isDirty && <span className="status-bar__dirty"> ●</span>}
      </span>
      <span className="status-bar__right">
        {ext && <span className="status-bar__badge">{ext.toUpperCase()}</span>}
      </span>
    </div>
  );
}
