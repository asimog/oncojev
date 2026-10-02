"""Reference proof derived from exact upstream examples and retained executions.

Qualification is operational history. These records never admit scientific evidence.
"""
import ast
import doctest
import math
from uuid import uuid4

from src.persistence.records import RecordKind, StoredRecord
from src.provenance import content_hash
from src.science.sandbox import SandboxMeasurementCandidate
from src.sources.models import ScientificArtifact


def operation_identity(candidate):
    request = candidate.request
    if request is None:
        raise ValueError('qualification requires retained operation inputs')
    return content_hash({'repository': candidate.receipt.repository_url, 'commit': candidate.receipt.commit_sha,
        'commands': {name: getattr(request, name) for name in ('install_command', 'test_command', 'execute_command')}})


def record_reference(record):
    return {'seq': record.seq, 'kind': record.kind.value, 'record_id': record.record_id, 'sha256': content_hash(record.payload)}


def resolve_record(store, reference, kind=None):
    record = store.record_at(reference['seq'])
    if (record is None or record.kind.value != reference.get('kind') or record.record_id != reference.get('record_id')
            or content_hash(record.payload) != reference.get('sha256') or kind is not None and record.kind != kind):
        raise ValueError('unresolved qualification reference')
    return record


def mean_reference_examples(source):
    """Extract upstream-authored values; never derive expectations from our wrapper."""
    module = ast.parse(source)
    function = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == 'mean')
    examples = []
    for example in doctest.DocTestParser().get_examples(ast.get_docstring(function) or ''):
        call = ast.parse(example.source.strip(), mode='eval').body
        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name) or call.func.id != 'mean' or len(call.args) != 1 or call.keywords:
            raise ValueError('unsupported upstream reference example')
        values = ast.literal_eval(call.args[0])
        rejected = bool(example.exc_msg)
        expected = None if rejected else float(ast.literal_eval(example.want.strip()))
        examples.append({'case_id': 'upstream-' + str(len(examples)), 'input_json': {'values': values},
            'kind': 'invalid' if rejected else 'canonical' if not examples else 'changed_input',
            'expected_values': None if rejected else {'mean': expected}, 'expected_error': 'ValueError' if rejected else None})
    if not {'canonical', 'changed_input', 'invalid'} <= {row['kind'] for row in examples}:
        raise ValueError('canonical, changed and invalid upstream examples required')
    return examples


def mean_scope_valid(scope):
    required = {'operation': 'finite_arithmetic_mean', 'missingness': 'reject', 'parameters': {},
        'interpretation': 'descriptive_retained_slice', 'units': 'same_declared_numeric_unit', 'entity_unit': 'record'}
    return all(scope.get(key) == value for key, value in required.items())


def declare_mean_reference(store, candidate_id, scope, source_reference, licence_reference, *, absolute_tolerance=1e-12):
    candidate_record = next((r for r in store.records(kind=RecordKind.SANDBOX_CANDIDATE) if r.record_id == candidate_id), None)
    if candidate_record is None:
        raise ValueError('resolved candidate required')
    candidate = SandboxMeasurementCandidate.model_validate(candidate_record.payload)
    source = ScientificArtifact.model_validate(resolve_record(store, source_reference, RecordKind.SCIENTIFIC_ARTIFACT).payload)
    licence = ScientificArtifact.model_validate(resolve_record(store, licence_reference, RecordKind.SCIENTIFIC_ARTIFACT).payload)
    for artifact in (source, licence):
        if artifact.source != 'github' or artifact.release != candidate.receipt.commit_sha or artifact.source_identity != candidate.receipt.repository_url:
            raise ValueError('source material must bind the actual immutable candidate')
    if source.request.get('path') != 'maths/average_mean.py' or licence.request.get('path') != 'LICENSE.md' or licence.licence != 'MIT':
        raise ValueError('inspected canonical operation and licence required')
    if not math.isfinite(absolute_tolerance) or not 0 <= absolute_tolerance <= 1e-12:
        raise ValueError('predeclared numerical tolerance must be bounded')
    if not mean_scope_valid(scope):
        raise ValueError('unsupported scientific scope; units and entity contract required')
    payload = {'version': 'mean-reference-spec-v1', 'candidate_id': candidate_id, 'candidate_sha256': content_hash(candidate_record.payload),
        'scope_sha256': content_hash(scope), 'scope': scope, 'operation_sha256': operation_identity(candidate),
        'source_reference': source_reference, 'licence_reference': licence_reference, 'absolute_tolerance': absolute_tolerance,
        'cases': mean_reference_examples(source.bytes().decode('utf-8')), 'parameters': {},
        'limitations': ['Upstream canonical examples establish numerical behavior, not oncology inference or population representativeness.']}
    return store.append(StoredRecord(kind=RecordKind.SERVICE_EVENT, record_id=uuid4().hex,
        payload={'event_type': 'CanonicalReferenceDeclared', 'operational_only': True, **payload}))


def evaluate_reference_validation(store, declaration_reference, comparison_references):
    declaration = resolve_record(store, declaration_reference, RecordKind.SERVICE_EVENT)
    spec = declaration.payload
    if spec.get('version') != 'mean-reference-spec-v1' or spec.get('event_type') != 'CanonicalReferenceDeclared':
        raise ValueError('unsupported reference declaration')
    for name in ('source_reference', 'licence_reference'):
        resolve_record(store, spec[name], RecordKind.SCIENTIFIC_ARTIFACT)
    candidate_record = next((r for r in store.records(kind=RecordKind.SANDBOX_CANDIDATE) if r.record_id == spec['candidate_id']), None)
    if candidate_record is None or content_hash(candidate_record.payload) != spec['candidate_sha256']:
        raise ValueError('reference candidate identity changed')
    observations = [resolve_record(store, ref, RecordKind.SERVICE_EVENT) for ref in comparison_references]
    by_case = {}
    for record in observations:
        row = record.payload
        if record.seq <= declaration.seq or row.get('event_type') != 'CanonicalReferenceComparison' or row.get('declaration_sha256') != content_hash(spec):
            raise ValueError('comparison must follow and bind its predeclared reference')
        if row['case_id'] in by_case:
            raise ValueError('duplicate reference comparison')
        by_case[row['case_id']] = (record, row)
    checks, results = {}, []
    for case in spec['cases']:
        entry = by_case.get(case['case_id'])
        record, row = entry if entry else (None, None)
        matched = False
        if row and row.get('input_sha256') == content_hash(case['input_json']) and row.get('operation_sha256') == spec['operation_sha256']:
            resource_records = [resolve_record(store, ref, RecordKind.LEDGER_EVENT) for ref in row.get('resource_references', [])]
            controls = [execution for observation in resource_records
                if declaration.seq < observation.seq < record.seq and observation.payload.get('event_type') == 'ScientificResourceReceipt'
                for execution in observation.payload.get('payload', {}).get('executions', [])]
            controlled = bool(controls) and all(p.get('kernel_controls_verified') is True and p.get('cleanup_confirmed') is True for p in controls)
            if case['expected_error']:
                matched = controlled and any(p.get('phase') == 'execute' and p.get('exit_code') != 0 for p in controls) and row.get('status') == 'rejected' and row.get('scientific_error') == case['expected_error']
            else:
                values = row.get('values', {})
                measured = next((r for r in store.records(kind=RecordKind.SANDBOX_CANDIDATE) if r.record_id == row.get('candidate_id')), None)
                upstream = next((r for r in store.records(kind=RecordKind.SANDBOX_CANDIDATE) if r.record_id == row.get('independent_candidate_id')), None)
                owned = False
                if measured is not None and upstream is not None:
                    actual = SandboxMeasurementCandidate.model_validate(measured.payload)
                    independent = SandboxMeasurementCandidate.model_validate(upstream.payload)
                    owned = (actual.values == values and operation_identity(actual) == spec['operation_sha256']
                        and actual.request.input_json == case['input_json'] and independent.request.input_json == case['input_json']
                        and independent.receipt.repository_url == actual.receipt.repository_url and independent.receipt.commit_sha == actual.receipt.commit_sha
                        and independent.values == row.get('independent_upstream_values')
                        and content_hash(actual.request.execute_command) == row.get('wrapper_command_sha256')
                        and content_hash(independent.request.execute_command) == row.get('independent_command_sha256'))
                matched = owned and controlled and row.get('status') == 'completed' and set(values) == set(case['expected_values']) and all(
                    isinstance(values[k], (int, float)) and not isinstance(values[k], bool) and math.isfinite(values[k])
                    and abs(values[k] - v) <= spec['absolute_tolerance'] for k, v in case['expected_values'].items())
                # Upstream source was executed independently of the wrapper.
                matched = matched and row.get('independent_upstream_values') == case['expected_values'] and row.get('independent_command_sha256') != row.get('wrapper_command_sha256')
        checks.setdefault(case['kind'], []).append(bool(matched))
        results.append({'case_id': case['case_id'], 'kind': case['kind'], 'matched': bool(matched)})
    scientific_scope_valid = mean_scope_valid(spec.get('scope', {}))
    source = ScientificArtifact.model_validate(resolve_record(store, spec['source_reference'], RecordKind.SCIENTIFIC_ARTIFACT).payload)
    scientific_scope_valid = scientific_scope_valid and spec['cases'] == mean_reference_examples(source.bytes().decode('utf-8'))
    passed = scientific_scope_valid and all(all(checks.get(kind, [False])) for kind in ('canonical', 'changed_input', 'invalid'))
    payload = {'version': 'reference-validation-v1', 'candidate_id': spec['candidate_id'], 'candidate_sha256': spec['candidate_sha256'],
        'scope_sha256': spec['scope_sha256'], 'status': 'passed' if passed else 'failed',
        'canonical_reference_matched': all(checks.get('canonical', [False])), 'changed_input_correct': all(checks.get('changed_input', [False])),
        'invalid_input_rejected': all(checks.get('invalid', [False])), 'scientific_scope_valid': scientific_scope_valid,
        'declaration_reference': declaration_reference, 'comparison_references': comparison_references, 'results': results,
        'limitations': spec['limitations']}
    return payload


def retain_reference_validation(store, declaration_reference, comparison_references):
    payload = evaluate_reference_validation(store, declaration_reference, comparison_references)
    return store.append(StoredRecord(kind=RecordKind.REFERENCE_VALIDATION, record_id=uuid4().hex, payload=payload))


def declare_environment_lock(store, candidate_id, scope, archive_reference, *, runtime_identity):
    """Recoverable stdlib-only operation; nonempty dependency sets are unsupported."""
    saved = next((r for r in store.records(kind=RecordKind.SANDBOX_CANDIDATE) if r.record_id == candidate_id), None)
    if saved is None or not mean_scope_valid(scope): raise ValueError('resolved scoped mean candidate required')
    candidate = SandboxMeasurementCandidate.model_validate(saved.payload)
    artifact = ScientificArtifact.model_validate(resolve_record(store, archive_reference, RecordKind.SCIENTIFIC_ARTIFACT).payload)
    if (artifact.byte_sha256 != candidate.receipt.environment.get('archive_sha256')
            or artifact.source_identity != candidate.receipt.repository_url or artifact.release != candidate.receipt.commit_sha):
        raise ValueError('recoverable archive must match actual candidate bytes/source')
    if candidate.request.dependency_wheels or candidate.request.install_command != ('python', '--version'):
        raise ValueError('dependency-bearing operations need a resolved transitive lock; unsupported')
    required = {'python_version', 'python_sha256', 'stdlib_sha256', 'platform', 'installer'}
    if set(runtime_identity) != required or any(not runtime_identity[key] for key in required):
        raise ValueError('complete runtime constraints and installer identity required')
    if any(runtime_identity[key] != candidate.receipt.environment.get(key) for key in ('python_version', 'python_sha256', 'platform')):
        raise ValueError('runtime identity differs from measured candidate')
    payload = {'event_type': 'EnvironmentLockDeclared', 'version': 'stdlib-environment-lock-v1', 'operational_only': True,
        'candidate_id': candidate_id, 'candidate_sha256': content_hash(saved.payload), 'scope_sha256': content_hash(scope),
        'operation_sha256': operation_identity(candidate), 'archive_reference': archive_reference,
        'repository_archive_sha256': artifact.byte_sha256, 'packages': [], 'runtime_identity': runtime_identity,
        'input_sha256': candidate.receipt.input_sha256, 'output_sha256': candidate.receipt.first_run.stdout_sha256,
        'limitations': ['Only the pinned stdlib-only operation and declared exact host Python constraints are supported.',
            'Fresh experiment recovery is separate from whole-host or arbitrary dependency recovery.']}
    return store.append(StoredRecord(kind=RecordKind.SERVICE_EVENT, record_id=uuid4().hex, payload=payload))


def recover_environment_inputs(store, lock_reference, *, runtime_identity, packages=()):
    lock = resolve_record(store, lock_reference, RecordKind.SERVICE_EVENT)
    payload = lock.payload
    if payload.get('version') != 'stdlib-environment-lock-v1' or payload.get('event_type') != 'EnvironmentLockDeclared':
        raise ValueError('unsupported environment lock')
    if list(packages) != payload['packages'] or packages:
        raise ValueError('conflicting or unsupported dependency pins')
    if runtime_identity != payload['runtime_identity']:
        raise ValueError('declared Python/stdlib/platform/installer drift')
    archive = ScientificArtifact.model_validate(resolve_record(store, payload['archive_reference'], RecordKind.SCIENTIFIC_ARTIFACT).payload)
    if archive.byte_sha256 != payload['repository_archive_sha256']:
        raise ValueError('recoverable archive identity mismatch')
    saved = next((r for r in store.records(kind=RecordKind.SANDBOX_CANDIDATE) if r.record_id == payload['candidate_id']), None)
    if saved is None or content_hash(saved.payload) != payload['candidate_sha256']:
        raise ValueError('environment candidate changed')
    candidate = SandboxMeasurementCandidate.model_validate(saved.payload)
    slug = candidate.receipt.repository_url.removeprefix('https://github.com/')
    return candidate, {'https://codeload.github.com/' + slug + '/tar.gz/' + candidate.receipt.commit_sha: archive.bytes()}


def evaluate_environment_qualification(store, lock_reference, fresh_candidate_reference, *, runtime_identity, failure_reference=None):
    lock = resolve_record(store, lock_reference, RecordKind.SERVICE_EVENT)
    original, inputs = recover_environment_inputs(store, lock_reference, runtime_identity=runtime_identity)
    fresh_environment = independent_replay = False
    references = {'lock_reference': lock_reference}
    if fresh_candidate_reference is not None:
        saved = resolve_record(store, fresh_candidate_reference, RecordKind.SANDBOX_CANDIDATE)
        fresh = SandboxMeasurementCandidate.model_validate(saved.payload)
        references['fresh_candidate_reference'] = fresh_candidate_reference
        fresh_environment = saved.seq > lock.seq and fresh.receipt.environment.get('experiment_path') != original.receipt.environment.get('experiment_path')
        controls = fresh.receipt.environment.get('process_resources', [])
        fresh_environment = fresh_environment and {p.get('phase') for p in controls} == {'prepare', 'install', 'test', 'execute', 'replay'} and all(
            p.get('cleanup_confirmed') is True and p.get('kernel_controls_verified') is True for p in controls)
        independent_replay = (operation_identity(fresh) == lock.payload['operation_sha256']
            and fresh.receipt.input_sha256 == lock.payload['input_sha256'] and fresh.values == original.values
            and fresh.receipt.first_run.stdout_sha256 == fresh.receipt.replay_run.stdout_sha256 == lock.payload['output_sha256']
            and fresh.receipt.environment.get('recovery_source') == 'retained_content_addressed_bytes'
            and fresh.receipt.environment.get('downloaded_bytes') == 0
            and fresh.receipt.environment.get('archive_sha256') == lock.payload['repository_archive_sha256']
            and all(fresh.receipt.environment.get(key) == runtime_identity[key] for key in ('python_version', 'python_sha256', 'platform')))
    elif failure_reference is not None:
        failure = resolve_record(store, failure_reference, RecordKind.SERVICE_EVENT)
        if failure.seq <= lock.seq: raise ValueError('recovery failure predates lock')
        references['failure_reference'] = failure_reference
    else:
        raise ValueError('actual fresh execution or retained failure required')
    passed = bool(fresh_environment and independent_replay)
    payload = {'version': 'environment-qualification-v1', 'status': 'passed' if passed else 'failed',
        'candidate_id': original.candidate_id, 'candidate_sha256': lock.payload['candidate_sha256'], 'scope_sha256': lock.payload['scope_sha256'],
        'fresh_environment': bool(fresh_environment), 'recoverable_lock': bool(inputs), 'independent_replay': bool(independent_replay),
        **references, 'runtime_identity': runtime_identity, 'limitations': lock.payload['limitations']}
    return payload


def retain_environment_qualification(store, lock_reference, fresh_candidate_reference, *, runtime_identity, failure_reference=None):
    payload = evaluate_environment_qualification(store, lock_reference, fresh_candidate_reference,
        runtime_identity=runtime_identity, failure_reference=failure_reference)
    return store.append(StoredRecord(kind=RecordKind.ENVIRONMENT_QUALIFICATION, record_id=uuid4().hex, payload=payload))


def scientific_qualification_resolves(store, kind, payload):
    try:
        if kind == RecordKind.REFERENCE_VALIDATION:
            actual = evaluate_reference_validation(store, payload['declaration_reference'], payload['comparison_references'])
        elif kind == RecordKind.ENVIRONMENT_QUALIFICATION:
            actual = evaluate_environment_qualification(store, payload['lock_reference'], payload.get('fresh_candidate_reference'),
                runtime_identity=payload['runtime_identity'], failure_reference=payload.get('failure_reference'))
        else:
            return False
        return actual == payload and actual['status'] == 'passed'
    except (ValueError, KeyError, TypeError):
        return False
