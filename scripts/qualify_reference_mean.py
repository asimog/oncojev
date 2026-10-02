"""Explicit native reference qualification for one pinned descriptive operation."""
import argparse
import asyncio
import base64
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from src.config.loader import load_models_config, load_runtime_config
from src.persistence.records import RecordKind, StoredRecord
from src.persistence.repository import ResearchRepository
from src.persistence.store import SqliteResearchStore
from src.provenance import content_hash
from src.runtime.pydantic_ai.factory import build_harness_runtime
from src.science.qualification import declare_mean_reference, operation_identity, record_reference, retain_reference_validation
from src.science.sandbox import GithubMethodRequest
from src.sources.models import ScientificArtifact


async def qualify(materials, output):
    root = Path(__file__).resolve().parents[1]
    runtime = build_harness_runtime(load_models_config(root / 'config/models.yaml'), load_runtime_config(root / 'config/runtime.yaml'))
    paths = runtime.runtime_paths
    paths.data.mkdir(parents=True, exist_ok=True)
    store = SqliteResearchStore(paths.database())
    runtime.repository = ResearchRepository(store)
    inspection = json.loads((materials / 'upstream-inspection.json').read_text())
    card = inspection['cards'][0]
    commit = card['metadata']['commit_sha']
    repository = card['homepage']
    scope = {'operation': 'finite_arithmetic_mean', 'missingness': 'reject', 'parameters': {},
        'interpretation': 'descriptive_retained_slice', 'units': 'same_declared_numeric_unit', 'entity_unit': 'record'}
    wrapper_command = ('python', str(root / 'src/science/reference_mean.py'), '/input/request.json')
    upstream_command = ('python', str(root / 'src/science/reference_upstream.py'), '/input/request.json')
    request = GithubMethodRequest(repository_url=repository, requested_ref=commit, install_command=('python', '--version'),
        test_command=('python', '-m', 'doctest', 'maths/average_mean.py'), execute_command=wrapper_command,
        input_json={'values': [3, 6, 9, 12, 15, 18, 21]})
    def block(label):
        value = runtime.manager.allocate(label, 'explicit native qualification; no scientific admission', 300)
        runtime.repository.record_block(value)
        return value.block_id
    try:
        owner = block('Pinned mean reference candidate')
        candidate = await runtime.execute_external(owner, request)
        lookup = store.append(StoredRecord(kind=RecordKind.EXTERNAL_LOOKUP, record_id=inspection['lookup_id'], payload=inspection, block_id=owner))
        artifacts = []
        for relative in ('maths/average_mean.py', 'LICENSE.md'):
            data = (materials / relative.replace('/', '-')).read_bytes()
            artifact = ScientificArtifact(block_id=owner, source='github', request={'path': relative}, source_identity=repository,
                release=commit, licence='MIT', format='text', provenance=(repository + '/blob/' + commit + '/' + relative,),
                content_base64=base64.b64encode(data).decode(), size_bytes=len(data), byte_sha256=hashlib.sha256(data).hexdigest())
            artifacts.append(record_reference(runtime.repository.record_scientific_artifact(artifact)))
        declaration = declare_mean_reference(store, candidate.candidate_id, scope, artifacts[0], artifacts[1])
        comparisons = []
        for case in declaration.payload['cases']:
            case_owner = block('Reference comparison ' + case['case_id'])
            variant = request.model_copy(update={'input_json': case['input_json']})
            row = {'event_type': 'CanonicalReferenceComparison', 'operational_only': True, 'case_id': case['case_id'],
                'declaration_sha256': content_hash(declaration.payload), 'operation_sha256': operation_identity(candidate),
                'input_sha256': content_hash(case['input_json']), 'wrapper_command_sha256': content_hash(wrapper_command),
                'independent_command_sha256': content_hash(upstream_command)}
            first_seq = store.count()
            try:
                result = await runtime.execute_external(case_owner, variant)
                row.update(status='completed', values=result.values, candidate_id=result.candidate_id)
                independent_owner = block('Independent upstream ' + case['case_id'])
                independent = await runtime.execute_external(independent_owner, variant.model_copy(update={'execute_command': upstream_command}))
                row['independent_upstream_values'] = independent.values
                row['independent_candidate_id'] = independent.candidate_id
            except Exception as error:
                row.update(status='rejected', error_type=type(error).__name__, error_detail=str(error),
                    scientific_error='ValueError' if 'ValueError' in str(error) else None)
            row['process_receipts'] = [execution for record in store.records(kind=RecordKind.LEDGER_EVENT)
                if record.seq > first_seq and record.payload.get('event_type') == 'ScientificResourceReceipt'
                for execution in record.payload.get('payload', {}).get('executions', [])]
            row['resource_references'] = [record_reference(r) for r in store.records(kind=RecordKind.LEDGER_EVENT)
                if r.seq > first_seq and r.payload.get('event_type') == 'ScientificResourceReceipt']
            saved = store.append(StoredRecord(kind=RecordKind.SERVICE_EVENT, record_id=uuid4().hex, block_id=case_owner, payload=row))
            comparisons.append(record_reference(saved))
            print(json.dumps({'case': case['case_id'], 'status': row['status']}), flush=True)
        proof = retain_reference_validation(store, record_reference(declaration), comparisons)
        output.parent.mkdir(parents=True, exist_ok=True)
        report = {'database': str(paths.database()), 'candidate_id': candidate.candidate_id, 'candidate_record': record_reference(
            next(r for r in store.records(kind=RecordKind.SANDBOX_CANDIDATE) if r.record_id == candidate.candidate_id)),
            'declaration_reference': record_reference(declaration), 'reference_validation': record_reference(proof),
            'reference_payload': proof.payload, 'scope': scope, 'lookup_reference': record_reference(lookup),
            'resources': runtime.service_resources.snapshot(), 'testing': paths.testing}
        output.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'status': proof.payload['status'], 'candidate': candidate.candidate_id, 'database': str(paths.database())}), flush=True)
        if proof.payload['status'] != 'passed': raise RuntimeError('reference qualification failed; observations retained')
    finally:
        await runtime.gdc.aclose()
        store.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--materials', type=Path, default=Path('var/task6-proof'))
    parser.add_argument('--output', type=Path, default=Path('var/task6-proof/reference-qualification.json'))
    args = parser.parse_args()
    asyncio.run(qualify(args.materials, args.output))


if __name__ == '__main__': main()
