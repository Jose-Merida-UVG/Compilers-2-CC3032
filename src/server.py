"""HTTP backend for the Compiscript IDE frontend.

Serves a small file-CRUD API over a `workspace/` directory (repo root) plus a
`/api/run` endpoint that lexes + parses a `.cps` file with the ANTLR-generated
Compiscript lexer/parser (see compiler.py) and returns errors, the printable
parse tree, and a JSON tree for the frontend's viewer.

Run with:
    PYTHONPATH=generated:src uvicorn server:app --app-dir src --reload --port 8080
"""
import shutil
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from compiler import analyze_file

ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = (ROOT / "workspace").resolve()
WORKSPACE.mkdir(exist_ok=True)

app = FastAPI(title="Compiscript backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── helpers ───────────────────────────────────────────────────────────────

def resolve(rel_path: str) -> Path:
    """Resolve a workspace-relative path, rejecting anything that escapes
    the workspace root (e.g. via '..')."""
    candidate = (WORKSPACE / rel_path).resolve()
    if candidate != WORKSPACE and WORKSPACE not in candidate.parents:
        raise HTTPException(status_code=400, detail="Invalid path")
    return candidate


def to_file_node(p: Path) -> dict:
    rel = p.relative_to(WORKSPACE).as_posix()
    if p.is_dir():
        children = sorted(p.iterdir(), key=lambda c: (not c.is_dir(), c.name.lower()))
        return {
            "name": p.name,
            "path": rel,
            "isDir": True,
            "children": [to_file_node(c) for c in children],
        }
    return {"name": p.name, "path": rel, "isDir": False}


# ── request bodies ───────────────────────────────────────────────────────

class FileWrite(BaseModel):
    path: str
    content: str = ""


class FileCreate(BaseModel):
    path: str


class RenameBody(BaseModel):
    oldPath: str
    newPath: str


class DirCreate(BaseModel):
    path: str


class RunBody(BaseModel):
    inputPath: str


# ── workspace tree ───────────────────────────────────────────────────────

@app.get("/api/workspace/tree")
def workspace_tree():
    children = sorted(WORKSPACE.iterdir(), key=lambda c: (not c.is_dir(), c.name.lower()))
    return [to_file_node(c) for c in children]


# ── file CRUD ─────────────────────────────────────────────────────────────

@app.get("/api/file", response_class=PlainTextResponse)
def read_file(path: str = Query(...)):
    p = resolve(path)
    if not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return p.read_text(encoding="utf-8")


@app.post("/api/file")
def write_file(body: FileWrite):
    p = resolve(body.path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body.content, encoding="utf-8")
    return {"ok": True}


@app.put("/api/file")
def create_file(body: FileCreate):
    p = resolve(body.path)
    if p.exists():
        raise HTTPException(status_code=409, detail="Already exists")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.touch()
    return {"ok": True}


@app.delete("/api/file")
def delete_file(path: str = Query(...)):
    p = resolve(path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="Not found")
    if p.is_dir():
        shutil.rmtree(p)
    else:
        p.unlink()
    return {"ok": True}


@app.post("/api/file/rename")
def rename_file(body: RenameBody):
    src = resolve(body.oldPath)
    dst = resolve(body.newPath)
    if not src.exists():
        raise HTTPException(status_code=404, detail="Not found")
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)
    return {"ok": True}


@app.put("/api/directory")
def create_directory(body: DirCreate):
    p = resolve(body.path)
    p.mkdir(parents=True, exist_ok=True)
    return {"ok": True}


# ── run (lex + parse) ────────────────────────────────────────────────────

@app.post("/api/run")
def run_file(body: RunBody):
    p = resolve(body.inputPath)
    if not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")
 
    result = analyze_file(str(p))
 
    lines = list(result["errors"]) + [result["status_message"], result["tree_string"]]
 
    out_dir = WORKSPACE / "output"
    out_dir.mkdir(exist_ok=True)
    (out_dir / f"{p.name}.out").write_text("\n".join(lines), encoding="utf-8")

    return {
        "lines": lines,
        "errors": result["errors"],
        "statusMessage": result["status_message"],
        "tree": result["tree_json"],
    }
