from __future__ import annotations

import json

import pytest
from antlr4 import InputStream

import compiler
from asm.generator import AsmResult


SOURCE = 'let x = 5; print(x);'
OUTPUTS = ('asm', 'asm_raw', 'asm_stats', 'activation')


def test_real_generator_is_connected():
    result = compiler.analyze(InputStream(SOURCE))
    assert result['errors'] == []
    assert 'main:' in result['asm']
    assert result['asm_stats']['instructions'] > 0
    assert isinstance(result['activation'], dict)


@pytest.mark.parametrize('source', ['let x = 1; @', 'let x = ;', 'print(missing);'])
def test_source_errors_never_invoke_assembly(monkeypatch, source):
    def forbidden(*args, **kwargs):
        pytest.fail('Se invocó P3 con errores del fuente')
    monkeypatch.setattr(compiler, 'generate_asm', forbidden)
    result = compiler.analyze(InputStream(source))
    assert result['errors']
    assert result['tac'] is None
    assert all(result[key] is None for key in OUTPUTS)


@pytest.mark.parametrize('stage', ['generate_asm', 'optimize'])
def test_internal_failure_clears_outputs(monkeypatch, stage):
    def fail(*args, **kwargs):
        raise RuntimeError('fallo de prueba')
    monkeypatch.setattr(compiler, stage, fail)
    result = compiler.analyze(InputStream(SOURCE))
    assert any('Error interno' in error for error in result['errors'])
    assert result['tac'] is None
    assert all(result[key] is None for key in OUTPUTS)


def test_json_boundary_raw_output_and_activation(monkeypatch):
    raw = ['.data', 'x: .word 0', '.text', 'main:', '    move $t0, $t0', '    jr $ra']
    activation = {'frames': {}, 'tree': {'label': '__main', 'children': []}}
    def generate(tac, table):
        assert all(isinstance(line, str) for line in tac)
        assert isinstance(table, dict)
        json.dumps(table)  # No checker ni nodos del árbol.
        return AsmResult(lines=list(raw), activation=activation)
    def optimize(lines):
        lines.remove('    move $t0, $t0')
        return lines, {'self_move': 1}
    monkeypatch.setattr(compiler, 'generate_asm', generate)
    monkeypatch.setattr(compiler, 'optimize', optimize)
    result = compiler.analyze(InputStream(SOURCE))
    assert result['errors'] == []
    assert result['asm_raw'] == raw
    assert result['asm_stats'] == {'instructions_raw': 2, 'instructions': 1, 'peephole': {'self_move': 1}}
    assert result['activation'] == activation
