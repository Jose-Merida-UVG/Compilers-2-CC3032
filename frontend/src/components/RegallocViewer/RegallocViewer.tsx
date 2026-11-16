import { useState } from "react";
import type { RegallocStep } from "../../types";
import "./RegallocViewer.css";

interface Props {
  data: RegallocStep[];
}

const REASONS: Record<string, string> = {
  "carga": "se cargó de su casa en memoria",
  "en registro": "ya estaba en un registro",
  "libre": "un registro libre",
  "reuso": "reusa el registro de un fuente que murió",
  "mismo registro": "ya estaba en ese registro",
  "spill": "se derramó otro valor a memoria para liberarlo",
  "flush": "se guardó a su casa en memoria",
};

/** Decisiones de `getReg` por instrucción TAC y el estado de los registros después de cada una. */
export default function RegallocViewer({ data }: Props) {
  const funcs = Array.from(new Set(data.map((s) => s.func)));
  const [selected, setSelected] = useState<string>(funcs[0] ?? "");
  const steps = data.filter((s) => s.func === selected);

  return (
    <div className="reg-viewer">
      <div className="reg-viewer__header">
        <span className="panel-title" style={{ padding: 0 }}>Selección de registros</span>
        <label className="reg-select">
          función
          <select value={selected} onChange={(e) => setSelected(e.target.value)}>
            {funcs.map((f) => <option key={f} value={f}>{f}</option>)}
          </select>
        </label>
      </div>
      <div className="reg-legend">
        {Object.entries(REASONS).map(([k, v]) => (
          <span key={k}><b className={`reg-tag reg-tag--${k.replace(" ", "-")}`}>{k}</b> {v}</span>
        ))}
        <span><b className="reg-dirty">*</b> sucio: más nuevo que su casa en memoria</span>
      </div>
      <div className="reg-viewer__body">
        <table className="reg-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Instrucción TAC</th>
              <th>Decisiones de getReg</th>
              <th>Registros al terminar</th>
            </tr>
          </thead>
          <tbody>
            {steps.map((s, i) => (
              <tr key={i}>
                <td className="reg-table__num">{i + 1}</td>
                <td className="reg-table__tac">{s.line}</td>
                <td>
                  {s.decisions.length === 0 ? <span className="reg-none">—</span> : s.decisions.map((d, j) => (
                    <span key={j} className="reg-decision" title={REASONS[d.reason] ?? d.reason}>
                      <span className="reg-decision__val">{d.op}</span>
                      <span className="reg-decision__arrow">→</span>
                      <span className="reg-decision__reg">{d.reg}</span>
                      <b className={`reg-tag reg-tag--${d.reason.replace(" ", "-")}`}>{d.reason}</b>
                    </span>
                  ))}
                </td>
                <td>
                  {Object.keys(s.regs).length === 0 ? <span className="reg-none">todos libres</span> : (
                    Object.entries(s.regs).map(([reg, val]) => (
                      <span key={reg} className="reg-cell">
                        <span className="reg-cell__reg">{reg}</span>
                        <span className="reg-cell__val">{val}{s.dirty.includes(reg) && <b className="reg-dirty">*</b>}</span>
                      </span>
                    ))
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
