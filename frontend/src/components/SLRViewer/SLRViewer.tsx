import { useState } from "react";
import type { SLRData } from "../../types";
import "./SLRViewer.css";

interface Props { data: SLRData; }

type Tab = "action" | "goto" | "sets" | "productions";

export default function SLRViewer({ data }: Props) {
  const [tab, setTab] = useState<Tab>("action");

  const stateIDs = Array.from(
    new Set([
      ...Object.keys(data.actions).map(Number),
      ...Object.keys(data.gotos).map(Number),
    ])
  ).sort((a, b) => a - b);

  // Fill missing states so every row appears even if it has no actions/gotos.
  const allStates = Array.from({ length: data.stateCount }, (_, i) => i);

  return (
    <div className="slr-viewer">
      {/* Stats bar */}
      <div className="slr-stats">
        <span>{data.stateCount} states</span>
        <span className="slr-sep">·</span>
        <span>{data.terminals.length} terminals</span>
        <span className="slr-sep">·</span>
        <span>{data.nonTerminals.length} non-terminals</span>
        <span className="slr-sep">·</span>
        <span>{data.productions.length} productions</span>
        {data.conflicts.length > 0 && (
          <>
            <span className="slr-sep">·</span>
            <span className="slr-conflict-badge">
              ⚠ {data.conflicts.length} conflict{data.conflicts.length > 1 ? "s" : ""}
            </span>
          </>
        )}
        {data.conflicts.length === 0 && (
          <>
            <span className="slr-sep">·</span>
            <span className="slr-ok-badge">✓ SLR(1)</span>
          </>
        )}
      </div>

      {/* Tab strip */}
      <div className="slr-tabs">
        {(["action", "goto", "sets", "productions"] as Tab[]).map((t) => (
          <button
            key={t}
            className={`slr-tab ${tab === t ? "slr-tab--active" : ""}`}
            onClick={() => setTab(t)}
          >
            {t === "action" ? "Action Table" :
             t === "goto"   ? "Goto Table" :
             t === "sets"   ? "FIRST / FOLLOW" :
             "Productions"}
          </button>
        ))}
      </div>

      <div className="slr-body">
        {tab === "action" && (
          <ActionTable
            states={allStates}
            terminals={data.terminals}
            actions={data.actions}
            conflicts={data.conflicts}
          />
        )}
        {tab === "goto" && (
          <GotoTable
            states={allStates}
            nonTerminals={data.nonTerminals}
            gotos={data.gotos}
          />
        )}
        {tab === "sets" && (
          <SetsTable
            nonTerminals={data.nonTerminals}
            first={data.first}
            follow={data.follow}
            startSymbol={data.startSymbol}
          />
        )}
        {tab === "productions" && (
          <ProductionsTable productions={data.productions} startSymbol={data.startSymbol} />
        )}
      </div>
    </div>
  );
}

// ── Action Table ──────────────────────────────────────────────────────────────

function ActionTable({ states, terminals, actions, conflicts }: {
  states: number[];
  terminals: string[];
  actions: Record<number, Record<string, string>>;
  conflicts: SLRData["conflicts"];
}) {
  const conflictSet = new Set(conflicts.map((c) => `${c.state}:${c.symbol}`));

  return (
    <div className="slr-table-wrap">
      <table className="slr-table">
        <thead>
          <tr>
            <th className="slr-th slr-th--state">State</th>
            {terminals.map((t) => (
              <th key={t} className="slr-th">{t}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {states.map((sid) => (
            <tr key={sid}>
              <td className="slr-td slr-td--state">{sid}</td>
              {terminals.map((t) => {
                const cell = actions[sid]?.[t] ?? "";
                const isConflict = conflictSet.has(`${sid}:${t}`);
                const kind = cell.startsWith("s") ? "shift"
                           : cell === "acc"        ? "accept"
                           : cell.startsWith("r")  ? "reduce"
                           : "";
                return (
                  <td
                    key={t}
                    className={`slr-td slr-td--${kind || "empty"} ${isConflict ? "slr-td--conflict" : ""}`}
                  >
                    {cell}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Goto Table ────────────────────────────────────────────────────────────────

function GotoTable({ states, nonTerminals, gotos }: {
  states: number[];
  nonTerminals: string[];
  gotos: Record<number, Record<string, number>>;
}) {
  return (
    <div className="slr-table-wrap">
      <table className="slr-table">
        <thead>
          <tr>
            <th className="slr-th slr-th--state">State</th>
            {nonTerminals.map((nt) => (
              <th key={nt} className="slr-th">{nt}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {states.map((sid) => (
            <tr key={sid}>
              <td className="slr-td slr-td--state">{sid}</td>
              {nonTerminals.map((nt) => {
                const target = gotos[sid]?.[nt];
                return (
                  <td key={nt} className={`slr-td ${target !== undefined ? "slr-td--goto" : "slr-td--empty"}`}>
                    {target !== undefined ? target : ""}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── FIRST / FOLLOW Table ──────────────────────────────────────────────────────

function SetsTable({ nonTerminals, first, follow, startSymbol }: {
  nonTerminals: string[];
  first: Record<string, string[]>;
  follow: Record<string, string[]>;
  startSymbol: string;
}) {
  return (
    <div className="slr-table-wrap">
      <table className="slr-table slr-table--sets">
        <thead>
          <tr>
            <th className="slr-th slr-th--nt">Non-terminal</th>
            <th className="slr-th">FIRST</th>
            <th className="slr-th">FOLLOW</th>
          </tr>
        </thead>
        <tbody>
          {nonTerminals.map((nt) => (
            <tr key={nt} className={nt === startSymbol ? "slr-tr--start" : ""}>
              <td className="slr-td slr-td--nt">
                {nt}
                {nt === startSymbol && <span className="slr-start-badge">start</span>}
              </td>
              <td className="slr-td slr-td--set">
                {"{" + (first[nt] ?? []).join(", ") + "}"}
              </td>
              <td className="slr-td slr-td--set">
                {"{" + (follow[nt] ?? []).join(", ") + "}"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Productions Table ─────────────────────────────────────────────────────────

function ProductionsTable({ productions, startSymbol }: {
  productions: SLRData["productions"];
  startSymbol: string;
}) {
  return (
    <div className="slr-table-wrap">
      <table className="slr-table slr-table--prods">
        <thead>
          <tr>
            <th className="slr-th slr-th--idx">#</th>
            <th className="slr-th">Head</th>
            <th className="slr-th">Body</th>
          </tr>
        </thead>
        <tbody>
          {productions.map((p, i) => (
            <tr key={i} className={p.head === startSymbol ? "slr-tr--start" : ""}>
              <td className="slr-td slr-td--idx">{i}</td>
              <td className="slr-td slr-td--head">{p.head}</td>
              <td className="slr-td slr-td--body">{p.body}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
