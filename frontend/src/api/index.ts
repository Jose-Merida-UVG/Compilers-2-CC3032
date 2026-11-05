import type { FileNode, RunOutput } from "../types";

const BASE = "/api";

async function req<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + url, init);
  if (!res.ok) {
    const body = await res.text();
    let msg = body;
    try { msg = JSON.parse(body).detail ?? JSON.parse(body).error ?? body; } catch { /* raw text */ }
    throw new Error(msg || `HTTP ${res.status}`);
  }
  const ct = res.headers.get("content-type") ?? "";
  return ct.includes("application/json")
    ? res.json()
    : (res.text() as unknown as T);
}

const json = (body: unknown) => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const api = {
  listDirectory: () =>
    req<FileNode[]>("/workspace/tree"),

  readFile: (path: string) =>
    req<string>(`/file?path=${encodeURIComponent(path)}`),

  writeFile: (path: string, content: string) =>
    req<void>("/file", json({ path, content })),

  createFile: (path: string) =>
    req<void>("/file", { ...json({ path }), method: "PUT" }),

  deleteFile: (path: string) =>
    req<void>(`/file?path=${encodeURIComponent(path)}`, { method: "DELETE" }),

  renameFile: (oldPath: string, newPath: string) =>
    req<void>("/file/rename", json({ oldPath, newPath })),

  createDirectory: (path: string) =>
    req<void>("/directory", { ...json({ path }), method: "PUT" }),

  run: async (inputPath: string): Promise<RunOutput> => {
    const result = await req<RunOutput>("/run", json({ inputPath }));
    return withMockAsm(result);
  },
};

/**
 * Desarrollo del IDE sin el generador: con `?mock` en la URL, si el backend
 * compiló sin errores pero todavía no manda ensamblador, se completa con los
 * datos de ejemplo de `mocks/sample.ts`. Sin `?mock` no hace nada.
 */
async function withMockAsm(result: RunOutput): Promise<RunOutput> {
  const wantsMock = new URLSearchParams(window.location.search).has("mock");
  if (!wantsMock || result.tac === null || result.asm !== undefined) return result;
  const m = await import("../mocks/sample");
  return {
    ...result,
    asm: m.mockAsm,
    asmRaw: m.mockAsmRaw,
    asmStats: m.mockAsmStats,
    activation: m.mockActivation,
  };
}
