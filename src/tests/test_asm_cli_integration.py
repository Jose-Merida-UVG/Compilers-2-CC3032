"""main.py --asm y server.py /api/run con el ensamblador (contrato P3 §8).

`compiler.analyze` ya se prueba en `tests/test_compiler_integration.py`; aquí
solo se verifica lo que viene después: lo que imprime el CLI, lo que devuelve y
guarda el servidor, y que con errores no quede ningún `.s` viejo (R9).
No ejecutan MARS.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

import compiler

VALIDO = "let x: integer = 5;\nprint(x * 2);\n"

def _cli(monkeypatch, capsys, tmp_path: Path, args: list[str], source: str = VALIDO):
    import main

    archivo = tmp_path / "p.cps"
    archivo.write_text(source, encoding="utf-8")
    argv = [str(archivo) if a == "FILE" else a for a in args]
    monkeypatch.setattr(sys, "argv", ["main.py", *argv])
    codigo = 0
    try:
        main.main()
    except SystemExit as exc:
        codigo = exc.code if isinstance(exc.code, int) else 1
    return codigo, capsys.readouterr()


def test_cli_por_defecto_sigue_imprimiendo_el_tac(monkeypatch, capsys, tmp_path):
    _codigo, salida = _cli(monkeypatch, capsys, tmp_path, ["FILE"])
    assert "func __main():" in salida.out
    assert ".globl" not in salida.out


def test_cli_asm_imprime_el_mips(monkeypatch, capsys, tmp_path):
    _codigo, salida = _cli(monkeypatch, capsys, tmp_path, ["--asm", "FILE"])
    assert ".globl main" in salida.out
    assert "func __main():" not in salida.out


def test_cli_asm_acepta_la_bandera_en_cualquier_posicion(monkeypatch, capsys, tmp_path):
    _codigo, salida = _cli(monkeypatch, capsys, tmp_path, ["FILE", "--asm"])
    assert ".globl main" in salida.out


def test_cli_asm_con_errores_no_imprime_mips(monkeypatch, capsys, tmp_path):
    _codigo, salida = _cli(monkeypatch, capsys, tmp_path, ["--asm", "FILE"], "print(z);\n")
    assert "no ha sido declarada" in salida.out
    assert ".globl" not in salida.out and ".text" not in salida.out


def test_cli_sin_archivo_muestra_el_uso(monkeypatch, capsys, tmp_path):
    codigo, salida = _cli(monkeypatch, capsys, tmp_path, [])
    assert codigo == 1 and "usage" in salida.err

@pytest.fixture
def cliente(tmp_path, monkeypatch):
    pytest.importorskip("httpx")  # lo necesita el TestClient de FastAPI
    from fastapi.testclient import TestClient

    import server

    monkeypatch.setattr(server, "WORKSPACE", tmp_path.resolve())
    return TestClient(server.app), tmp_path


def _corre(c, nombre: str, contenido: str) -> dict:
    assert c.post("/api/file", json={"path": nombre, "content": contenido}).status_code == 200
    r = c.post("/api/run", json={"inputPath": nombre})
    assert r.status_code == 200
    return r.json()


def test_server_devuelve_asm_stats_y_activacion(cliente):
    c, _ws = cliente
    r = _corre(c, "p.cps", VALIDO)
    assert r["errors"] == []
    assert r["asm"] and r["asmRaw"]
    assert r["asmStats"]["instructions"] > 0
    assert isinstance(r["activation"], dict)


def test_server_guarda_el_s_con_el_nombre_que_espera_el_ide(cliente):
    c, ws = cliente
    r = _corre(c, "p.cps", VALIDO)
    guardado = ws / "output" / "p" / "p.cps.s"  
    assert guardado.read_text(encoding="utf-8").splitlines() == r["asm"]


def test_server_con_errores_devuelve_null_y_borra_el_s_viejo(cliente):
    c, ws = cliente
    _corre(c, "p.cps", VALIDO)
    guardado = ws / "output" / "p" / "p.cps.s"
    assert guardado.exists()
    r = _corre(c, "p.cps", "print(z);\n")
    assert r["errors"]
    assert r["asm"] is None and r["asmRaw"] is None
    assert r["asmStats"] is None and r["activation"] is None
    assert not guardado.exists()


def test_server_fallo_interno_del_generador_no_deja_s_viejo(cliente, monkeypatch):
    c, ws = cliente
    _corre(c, "p.cps", VALIDO)
    guardado = ws / "output" / "p" / "p.cps.s"
    assert guardado.exists()

    def falla(*_args, **_kwargs):
        raise RuntimeError("fallo de prueba")

    monkeypatch.setattr(compiler, "generate_asm", falla)
    r = _corre(c, "p.cps", VALIDO)
    assert any("Error interno" in e for e in r["errors"])
    assert r["asm"] is None
    assert not guardado.exists()
