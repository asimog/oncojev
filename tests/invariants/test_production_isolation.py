"""Production must construct and resolve qualification without evaluation files."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
from scripts.check_architecture import check_imports


@pytest.mark.parametrize('source', [
    'from evals.reference import evaluate_reference_cases',
    'from src import evals',
    'from ..evals import models',
    'import tests.invariants.test_evaluation',
    'import pytest',
    'import importlib as loader; loader.import_module("evals.harness")',
    'from importlib import import_module as load; load("src.evals.reference")',
    '__import__("tests.helper")',
    'from builtins import __import__ as load; load("evals")',
    'import importlib; importlib.import_module(".evals", package="src")',
    'import importlib; importlib.import_module(module_name)',
])
def test_production_import_guard_rejects_evaluation_and_test_dependencies(tmp_path, source):
    path = tmp_path / 'src' / 'owner' / 'consumer.py'
    path.parent.mkdir(parents=True)
    path.write_text(source + '\n')
    with pytest.raises(ValueError, match='production'):
        check_imports(tmp_path)


def test_import_guard_allows_evaluation_callers_and_production_literal_imports(tmp_path):
    production = tmp_path / 'src' / 'owner.py'
    production.parent.mkdir()
    production.write_text('import importlib; importlib.import_module("src.science.models")\n')
    evaluation = tmp_path / 'evals' / 'consumer.py'
    evaluation.parent.mkdir()
    evaluation.write_text('from src.autonomous import AutonomousService\nimport pytest\n')
    check_imports(tmp_path)


def test_fresh_production_consumers_work_without_evaluation_or_history(tmp_path):
    root = Path(__file__).resolve().parents[2]
    application = tmp_path / 'application'
    shutil.copytree(root / 'src', application / 'src',
                    ignore=shutil.ignore_patterns('evals', 'results', 'proven', '__pycache__'))
    shutil.copytree(root / 'config', application / 'config')
    shutil.copy2(root / 'pyproject.toml', application / 'pyproject.toml')
    code = '''
import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from src.oncolab.governance import CapabilityProposal
from src.oncolab.reusable import resolve_reusable_method
from src.oncolab.utility import retain_utility_evaluation, utility_evaluation_resolves
from src.autonomous import service_from_environment
from src.runtime.pydantic_ai.factory import build_system
from src.persistence.records import RecordKind, StoredRecord
from src.provenance import content_hash
service = service_from_environment(Path.cwd())
assert service.store.records() == ()
system = build_system(service.models, service.policy, repository=service.repository,
                      resources=service.resources, paths=service.paths)
assert len(service.store.records(kind=RecordKind.REGISTRY_REVISION)) == 1
assert not service.store.records(kind=RecordKind.INSTITUTIONAL_OBSERVATION)
assert not utility_evaluation_resolves(service.store, {}, system.runtime.institution.application)
service.store.append(StoredRecord(kind=RecordKind.SANDBOX_CANDIDATE, record_id='contract-fixture',
                                 payload={'provenance': 'explicit unsupported contract fixture'}))
scope = {'operation': 'contract_fixture'}
proof = retain_utility_evaluation(service.store, 'contract-fixture', scope,
    {'mode': 'deterministic', 'repeats': 1, 'rows': [{'observations': {
        'candidate_id': 'contract-fixture', 'scope_sha256': content_hash(scope)}}]},
    application_identity=system.runtime.institution.application)
assert proof.payload['status'] == 'unsupported'
assert not utility_evaluation_resolves(service.store, proof.payload, system.runtime.institution.application)
assert not service.store.records(kind=RecordKind.EVIDENCE)
assert not any(name == 'evals' or name.startswith(('evals.', 'src.evals', 'tests.')) for name in sys.modules)
async def close_clients():
    for client in (system.runtime.gdc, system.runtime.xena, system.runtime.literature):
        await client.aclose()
asyncio.run(close_clients())
service.close()
print('production isolation passed')
'''
    environment = {**os.environ, 'ONCOJEV_TESTING': '0', 'ONCOJEV_DATA_ROOT': str(tmp_path / 'data'),
                   'OPENROUTER_API_KEY': 'fixture', 'TYPESAFE_API_KEY': 'fixture',
                   'LOGFIRE_SEND_TO_LOGFIRE': 'false'}
    environment.pop('ONCOJEV_DB_PATH', None)
    result = subprocess.run([sys.executable, '-I', '-B', '-c', code], cwd=application,
                            env=environment, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().endswith('production isolation passed')
