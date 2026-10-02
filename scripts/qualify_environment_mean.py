"""Explicit offline fresh installation/replay from a retained source lock."""
import asyncio
import base64
import hashlib
import json
from pathlib import Path
import platform
import sys
from uuid import uuid4

from src.config.loader import load_models_config, load_runtime_config
from src.persistence.records import RecordKind, StoredRecord
from src.persistence.repository import ResearchRepository
from src.persistence.store import SqliteResearchStore
from src.runtime.pydantic_ai.factory import build_harness_runtime
from src.runtime.verification import environment_basis
from src.science.qualification import (declare_environment_lock, recover_environment_inputs,
    retain_environment_qualification, record_reference, resolve_record)
from src.science.sandbox import SandboxMeasurementCandidate
from src.sources.models import ScientificArtifact


async def main():
    root = Path(__file__).resolve().parents[1]
    reference = json.loads((root / 'var/task6-proof/reference-qualification-corrected.json').read_text())
    store = SqliteResearchStore(reference['database'])
    policy = load_runtime_config(root / 'config/runtime.yaml')
    runtime = build_harness_runtime(load_models_config(root / 'config/models.yaml'), policy, repository=ResearchRepository(store))
    try:
        candidate = SandboxMeasurementCandidate.model_validate(resolve_record(store, reference['candidate_record'], RecordKind.SANDBOX_CANDIDATE).payload)
        data = (Path(candidate.receipt.environment['experiment_path']) / 'inputs/repository.tar.gz').read_bytes()
        artifact = ScientificArtifact(block_id=next(r.block_id for r in store.records(kind=RecordKind.SANDBOX_CANDIDATE) if r.record_id == candidate.candidate_id),
            source='github', request={'path': 'repository.tar.gz'}, source_identity=candidate.receipt.repository_url,
            release=candidate.receipt.commit_sha, licence='MIT', format='gzip', provenance=('Retained exact acquired source archive; not scientific evidence',),
            content_base64=base64.b64encode(data).decode(), size_bytes=len(data), byte_sha256=hashlib.sha256(data).hexdigest())
        saved = runtime.repository.record_scientific_artifact(artifact)
        basis = environment_basis(policy, runtime.runtime_paths)
        identity = {'python_version': platform.python_version(), 'python_sha256': hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest(),
            'stdlib_sha256': basis['stdlib_sha256'], 'platform': platform.platform(),
            'installer': hashlib.sha256((root / 'src/science/prepare_exec.py').read_bytes()).hexdigest()}
        lock = declare_environment_lock(store, candidate.candidate_id, reference['scope'], record_reference(saved), runtime_identity=identity)
        original, inputs = recover_environment_inputs(store, record_reference(lock), runtime_identity=identity)
        block = runtime.manager.allocate('Recover pinned mean from exact retained bytes', 'explicit fresh environment qualification', 300)
        runtime.repository.record_block(block)
        fresh = await runtime.execute_external(block.block_id, original.request.model_copy(update={'requested_ref': original.receipt.commit_sha}), recovery_inputs=inputs)
        fresh_record = next(r for r in store.records(kind=RecordKind.SANDBOX_CANDIDATE) if r.record_id == fresh.candidate_id)
        after = environment_basis(policy, runtime.runtime_paths)
        if after['stdlib_sha256'] != identity['stdlib_sha256']:
            raise RuntimeError('standard library changed during fresh recovery; no qualification')
        proof = retain_environment_qualification(store, record_reference(lock), record_reference(fresh_record), runtime_identity=identity)
        adverse = []
        for label, options in [('conflicting-pins', {'packages': [{'name': 'numpy', 'version': '1'}, {'name': 'numpy', 'version': '2'}]}),
                ('runtime-drift', {'runtime_identity': {**identity, 'python_sha256': '0' * 64}}),
                ('unresolved-lock', {'lock_reference': {**record_reference(lock), 'sha256': '0' * 64}})]:
            arguments = {'lock_reference': record_reference(lock), 'runtime_identity': identity, **options}
            try: recover_environment_inputs(store, **arguments)
            except ValueError as error:
                observation = store.append(StoredRecord(kind=RecordKind.SERVICE_EVENT, record_id=uuid4().hex,
                    payload={'event_type': 'EnvironmentRecoveryAdverse', 'case': label, 'status': 'rejected', 'error_type': type(error).__name__,
                        'detail': str(error), 'lock_reference': record_reference(lock), 'operational_only': True}))
                adverse.append(record_reference(observation))
            else: raise AssertionError(label + ' silently passed')
        # A missing retained archive must never fall back to downloading it.
        unavailable = runtime.manager.allocate('Missing retained package recovery', 'explicit adverse qualification', 300)
        runtime.repository.record_block(unavailable)
        try: await runtime.execute_external(unavailable.block_id, original.request.model_copy(update={'requested_ref': original.receipt.commit_sha}), recovery_inputs={})
        except Exception as error:
            assert 'network fallback forbidden' in str(error)
            observation = store.append(StoredRecord(kind=RecordKind.SERVICE_EVENT, record_id=uuid4().hex,
                payload={'event_type': 'EnvironmentRecoveryAdverse', 'case': 'unavailable-retained-package', 'status': 'rejected',
                    'error_type': type(error).__name__, 'detail': str(error), 'lock_reference': record_reference(lock), 'operational_only': True}))
            adverse.append(record_reference(observation))
            failed = retain_environment_qualification(store, record_reference(lock), None, runtime_identity=identity, failure_reference=record_reference(observation))
            assert failed.payload['status'] == 'failed'
        else: raise AssertionError('missing package recovered through network')
        report = {'database': reference['database'], 'scope': reference['scope'], 'candidate_id': candidate.candidate_id,
            'lock_reference': record_reference(lock), 'qualification_reference': record_reference(proof), 'qualification': proof.payload,
            'fresh_candidate_reference': record_reference(fresh_record), 'adverse_references': adverse,
            'network_acquisition_bytes': fresh.receipt.environment['downloaded_bytes'], 'recovered_bytes': fresh.receipt.environment['recovered_bytes']}
        output = root / 'var/task7-proof'; output.mkdir(exist_ok=True)
        (output / 'environment-qualification.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'status': proof.payload['status'], 'fresh_environment': proof.payload['fresh_environment'],
            'network_bytes': report['network_acquisition_bytes'], 'recovered_bytes': report['recovered_bytes'], 'adverse_cases': len(adverse)}), flush=True)
        assert proof.payload['status'] == 'passed'
    finally:
        await runtime.gdc.aclose(); store.close()


if __name__ == '__main__': asyncio.run(main())
