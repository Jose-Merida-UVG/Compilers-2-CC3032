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

  run: (inputPath: string) =>
    req<RunOutput>("/run", json({ inputPath })),
};
