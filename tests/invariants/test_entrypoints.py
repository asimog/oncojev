"""Operational launchers delegate to the canonical CLI/service owner."""
import importlib
import inspect
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


class ServiceCapture:
    def __init__(self): self.calls = []
    def run_once(self, direction):
        self.calls.append(('cycle', direction))
        return SimpleNamespace(mode=SimpleNamespace(value='live'), direction=direction,
            director_output='', block_ids=('block',), dossiers=(), status=SimpleNamespace(value='complete'),
            director_outcome=SimpleNamespace(value='returned'), director_error_type=None)
    def serve(self, host, port, direction, interval):
        self.calls.append(('serve', host, port, direction, interval))
    def close(self): self.calls.append(('close',))


@pytest.mark.parametrize('name', ['src.__main__', 'scripts.run_live_cycle', 'scripts.run_live_phase3'])
def test_one_shot_entrypoints_preserve_supplied_direction_and_close(monkeypatch, name):
    cli = importlib.import_module('src.__main__')
    module = importlib.import_module(name)
    service = ServiceCapture()
    roots = []
    def create(root): roots.append(root); return service
    monkeypatch.setattr(cli, 'service_from_environment', create)
    # Isolate old launcher bindings while reproducing their bypass safely.
    if module is not cli and hasattr(module, 'service_from_environment'):
        monkeypatch.setattr(module, 'service_from_environment', create)
    if hasattr(module, 'load_local_environment'):
        monkeypatch.setattr(module, 'load_local_environment', lambda root: None)
    monkeypatch.setenv('OPENROUTER_API_KEY', 'fixture')
    monkeypatch.setenv('TYPESAFE_API_KEY', 'fixture')
    args = ['launcher'] + (['cycle'] if module is cli else []) + ['--direction', 'A broad research direction']
    monkeypatch.setattr(sys, 'argv', args)
    result = module.main()
    if inspect.iscoroutine(result): result.close()
    assert service.calls == [('cycle', 'A broad research direction'), ('close',)]
    assert roots == [Path(cli.__file__).resolve().parents[1]]


def test_serve_entrypoint_passes_operational_settings_to_same_service(monkeypatch):
    from src import __main__ as cli
    service = ServiceCapture()
    monkeypatch.setattr(cli, 'service_from_environment', lambda root: service)
    monkeypatch.setenv('HOST', '127.0.0.1')
    monkeypatch.setenv('PORT', '9090')
    monkeypatch.setenv('ONCOJEV_AUTONOMOUS_INTERVAL_SECONDS', '12')
    monkeypatch.setattr(sys, 'argv', ['launcher', 'serve', '--direction', 'Another broad direction'])
    cli.main()
    assert service.calls == [('serve', '127.0.0.1', 9090, 'Another broad direction', 12)]


def test_worker_exec_preserves_canonical_module_command(monkeypatch):
    from scripts import worker_entrypoint
    calls = []
    monkeypatch.setattr(worker_entrypoint.os, 'getuid', lambda: 1000)
    monkeypatch.setattr(worker_entrypoint.os, 'execv', lambda executable, argv: calls.append((executable, argv)))
    monkeypatch.setattr(sys, 'argv', ['worker', '-m', 'src', 'serve'])
    worker_entrypoint.main()
    assert calls == [(sys.executable, [sys.executable, '-m', 'src', 'serve'])]
