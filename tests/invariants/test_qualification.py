"""Proof integrity contracts; synthetic records do not constitute native proof."""
import base64
import hashlib

import pytest

from src.persistence.records import RecordKind, StoredRecord
from src.persistence.store import SqliteResearchStore
from src.provenance import content_hash
from src.science.qualification import declare_mean_reference, mean_reference_examples, record_reference, retain_reference_validation
from src.science.sandbox import GithubMethodRequest, SandboxInvocation, SandboxMeasurementCandidate, SandboxReceipt
from src.sources.models import ScientificArtifact


SOURCE = '''def mean(values):
    """
    >>> mean([1, 2])
    1.5
    >>> mean([2, 4])
    3.0
    >>> mean([])
    Traceback (most recent call last):
        ...
    ValueError: empty
    """
    if not values: raise ValueError('empty')
    return sum(values) / len(values)
'''
SCOPE = {'operation': 'finite_arithmetic_mean', 'missingness': 'reject', 'parameters': {},
    'interpretation': 'descriptive_retained_slice', 'units': 'same_declared_numeric_unit', 'entity_unit': 'record'}


def fixture(store):
    request = GithubMethodRequest(repository_url='https://github.com/example/fixture', requested_ref='a' * 40,
        install_command=('python', '--version'), test_command=('python', 'test.py'), execute_command=('python', 'wrapper.py'), input_json={'values': [1, 2]})
    invocation = SandboxInvocation(command=request.execute_command, exit_status=0, stdout_sha256='b' * 64, stderr_sha256='c' * 64)
    receipt = SandboxReceipt(repository_url=request.repository_url, commit_sha='a' * 40, environment={}, environment_sha256=content_hash({}),
        input_sha256=content_hash(request.input_json), install=invocation, test=invocation, first_run=invocation, replay_run=invocation)
    candidate = SandboxMeasurementCandidate(candidate_id='fixture', request=request, receipt=receipt, values={'mean': 1.5})
    store.append(StoredRecord(kind=RecordKind.SANDBOX_CANDIDATE, record_id='fixture', payload=candidate.model_dump(mode='json')))
    refs = []
    for path, data in [('maths/average_mean.py', SOURCE.encode()), ('LICENSE.md', b'MIT fixture licence')]:
        artifact = ScientificArtifact(block_id='fixture-block', source='github', source_identity=request.repository_url,
            request={'path': path}, release='a' * 40, licence='MIT', format='text', provenance=('synthetic integrity fixture',),
            content_base64=base64.b64encode(data).decode(), size_bytes=len(data), byte_sha256=hashlib.sha256(data).hexdigest())
        refs.append(record_reference(store.append(StoredRecord(kind=RecordKind.SCIENTIFIC_ARTIFACT, record_id=artifact.artifact_id,
            payload=artifact.model_dump(mode='json')))))
    return candidate, refs


def test_passing_flags_and_expected_values_without_owned_execution_cannot_qualify():
    store = SqliteResearchStore()
    try:
        candidate, refs = fixture(store)
        declaration = declare_mean_reference(store, candidate.candidate_id, SCOPE, *refs)
        comparisons = []
        for case in declaration.payload['cases']:
            resources = store.append(StoredRecord(kind=RecordKind.LEDGER_EVENT, record_id=case['case_id'] + ':resources',
                payload={'event_type': 'ScientificResourceReceipt', 'payload': {'executions': [
                    {'phase': 'execute', 'exit_code': 1 if case['expected_error'] else 0,
                     'kernel_controls_verified': True, 'cleanup_confirmed': True}]}}))
            row = {'event_type': 'CanonicalReferenceComparison', 'case_id': case['case_id'],
                'declaration_sha256': content_hash(declaration.payload), 'operation_sha256': declaration.payload['operation_sha256'],
                'input_sha256': content_hash(case['input_json']), 'values': case['expected_values'],
                'independent_upstream_values': case['expected_values'], 'scientific_error': case['expected_error'],
                'status': 'rejected' if case['expected_error'] else 'completed', 'resource_references': [record_reference(resources)],
                'wrapper_command_sha256': 'x', 'independent_command_sha256': 'y'}
            comparisons.append(record_reference(store.append(StoredRecord(kind=RecordKind.SERVICE_EVENT, record_id=case['case_id'], payload=row))))
        proof = retain_reference_validation(store, record_reference(declaration), comparisons)
        assert proof.payload['status'] == 'failed'
        assert not proof.payload['canonical_reference_matched'] and not proof.payload['changed_input_correct']
        tampered = {**comparisons[0], 'sha256': '0' * 64}
        with pytest.raises(ValueError, match='unresolved'):
            retain_reference_validation(store, record_reference(declaration), [tampered])
        assert not store.records(kind=RecordKind.EVIDENCE)
    finally:
        store.close()


def test_upstream_source_and_scope_are_required_before_reference_comparison():
    assert [case['expected_values'] for case in mean_reference_examples(SOURCE)] == [{'mean': 1.5}, {'mean': 3.0}, None]
    store = SqliteResearchStore()
    try:
        candidate, refs = fixture(store)
        for scope in ({**SCOPE, 'parameters': {'weights': [1, 2]}}, {**SCOPE, 'interpretation': 'population_effect'}):
            with pytest.raises(ValueError, match='scientific scope'):
                declare_mean_reference(store, candidate.candidate_id, scope, *refs)
        with pytest.raises(ValueError, match='tolerance'):
            declare_mean_reference(store, candidate.candidate_id, SCOPE, *refs, absolute_tolerance=1)
        assert not store.records(kind=RecordKind.REFERENCE_VALIDATION)
    finally:
        store.close()


def test_retained_recovery_never_falls_back_to_network_and_counts_local_bytes(tmp_path, monkeypatch):
    from src.science.local import LocalVenvScientificBackend
    from src.science.sandbox import SandboxError
    import httpx
    def forbidden(*args, **kwargs):
        raise AssertionError('recovery attempted network access')
    monkeypatch.setattr(httpx, 'Client', forbidden)
    backend = LocalVenvScientificBackend(tmp_path, download_limit=4, recovery_inputs={'https://fixture/package': b'data'})
    assert backend._fetch('https://fixture/package') == b'data'
    assert backend.downloaded == 0 and backend.recovered_bytes == 4
    with pytest.raises(SandboxError, match='network fallback forbidden'):
        backend._fetch('https://fixture/unavailable')
    backend.recovery_inputs['https://fixture/oversized'] = b'large'
    with pytest.raises(SandboxError, match='oversized'):
        backend._fetch('https://fixture/oversized')
    assert backend.downloaded == 0


def test_environment_lock_rejects_runtime_pin_and_content_drift():
    from src.science.qualification import declare_environment_lock, recover_environment_inputs, retain_environment_qualification
    store = SqliteResearchStore()
    try:
        candidate, _ = fixture(store)
        data = b'controlled archive integrity fixture; no native execution'
        identity = {'python_version': 'fixture', 'python_sha256': 'd' * 64, 'stdlib_sha256': 'e' * 64, 'platform': 'fixture', 'installer': 'f' * 64}
        environment = {'python_version': identity['python_version'], 'python_sha256': identity['python_sha256'],
            'platform': identity['platform'], 'archive_sha256': hashlib.sha256(data).hexdigest(), 'experiment_path': '/fixture/original'}
        original = candidate.model_copy(update={'candidate_id': 'environment-fixture', 'receipt': candidate.receipt.model_copy(update={
            'environment': environment, 'environment_sha256': content_hash(environment)})})
        store.append(StoredRecord(kind=RecordKind.SANDBOX_CANDIDATE, record_id=original.candidate_id, payload=original.model_dump(mode='json')))
        artifact = ScientificArtifact(block_id='fixture', source='github', request={}, source_identity=original.receipt.repository_url,
            release=original.receipt.commit_sha, format='gzip', provenance=('controlled integrity fixture, not runnable reference',),
            content_base64=base64.b64encode(data).decode(), size_bytes=len(data), byte_sha256=hashlib.sha256(data).hexdigest())
        saved = store.append(StoredRecord(kind=RecordKind.SCIENTIFIC_ARTIFACT, record_id=artifact.artifact_id, payload=artifact.model_dump(mode='json')))
        lock = declare_environment_lock(store, original.candidate_id, SCOPE, record_reference(saved), runtime_identity=identity)
        with pytest.raises(ValueError, match='drift'):
            recover_environment_inputs(store, record_reference(lock), runtime_identity={**identity, 'python_sha256': '0' * 64})
        with pytest.raises(ValueError, match='dependency pins'):
            recover_environment_inputs(store, record_reference(lock), runtime_identity=identity, packages=({'name': 'fixture', 'version': '1'},))
        with pytest.raises(ValueError, match='unresolved'):
            recover_environment_inputs(store, {**record_reference(lock), 'sha256': '0' * 64}, runtime_identity=identity)
        fresh_environment = {**environment, 'experiment_path': '/fixture/fresh', 'recovery_source': 'retained_content_addressed_bytes', 'downloaded_bytes': 0}
        fresh = original.model_copy(update={'candidate_id': 'unobserved-fresh', 'receipt': original.receipt.model_copy(update={
            'environment': fresh_environment, 'environment_sha256': content_hash(fresh_environment)})})
        fresh_record = store.append(StoredRecord(kind=RecordKind.SANDBOX_CANDIDATE, record_id=fresh.candidate_id, payload=fresh.model_dump(mode='json')))
        proof = retain_environment_qualification(store, record_reference(lock), record_reference(fresh_record), runtime_identity=identity)
        assert proof.payload['status'] == 'failed' and not proof.payload['fresh_environment']
        assert not store.records(kind=RecordKind.EVIDENCE)
    finally:
        store.close()


def test_reusable_mean_requires_declared_units_complete_rows_and_unique_entities():
    from src.science.reusable import extract_mean_input
    from src.sources.models import AcquisitionRecord
    source = AcquisitionRecord(source='fixture', request={'field_units': {'value': 'years'}},
        records=({'id': 'a', 'value': 30}, {'id': 'b', 'value': 50}), provenance=('integrity fixture',))
    values, lineage = extract_mean_input(source, 'value', 'id', 'years')
    assert values == {'values': [30, 50]} and lineage['entities'] == ['a', 'b']
    for modified in (source.model_copy(update={'origin': 'synthetic'}), source.model_copy(update={'request': {}}),
        source.model_copy(update={'records': ({'id': 'a', 'value': None},)}),
        source.model_copy(update={'records': ({'id': 'a', 'value': 30}, {'id': 'a', 'value': 50})})):
        with pytest.raises(ValueError): extract_mean_input(modified, 'value', 'id', 'years')
    with pytest.raises(ValueError, match='unit'): extract_mean_input(source, 'value', 'id', 'days')


def test_method_utility_flags_without_independent_review_do_not_pass():
    from src.evals.reference import retain_utility_evaluation, utility_evaluation_resolves
    store = SqliteResearchStore()
    try:
        candidate, _ = fixture(store)
        report = {'mode': 'live', 'repeats': 3, 'scientific_utility': 1, 'rows': [
            {'independent_review': 'reviewed', 'agreement': True, 'observations': {
                'candidate_id': candidate.candidate_id, 'scope_sha256': content_hash(SCOPE)}}]}
        proof = retain_utility_evaluation(store, candidate.candidate_id, SCOPE, report, application_identity='fixture')
        assert proof.payload['status'] == 'unsupported'
        assert not utility_evaluation_resolves(store, {**proof.payload, 'status': 'passed'}, 'fixture')
        assert not store.records(kind=RecordKind.EVIDENCE)
    finally: store.close()


def test_passing_reference_flags_cannot_replace_resolved_observations():
    from src.science.qualification import scientific_qualification_resolves
    store = SqliteResearchStore()
    try:
        assert not scientific_qualification_resolves(store, RecordKind.REFERENCE_VALIDATION,
            {'status': 'passed', 'canonical_reference_matched': True, 'changed_input_correct': True,
             'invalid_input_rejected': True, 'scientific_scope_valid': True})
    finally: store.close()


def test_search_metadata_migration_preserves_routes_history_and_cursor_identity():
    from src.oncolab.catalogue import initial_oncolab_index
    from src.oncolab.registry import OncoLabIndex
    from src.oncolab.institution import OncoLabInstitution, refresh_reviewed_search_metadata
    store = SqliteResearchStore()
    try:
        seed = initial_oncolab_index()
        descriptors = [d.model_copy(update={'purpose': 'Original generic numerical metadata', 'tags': ('statistics',)})
            if d.capability_id == 'stat.scipy' else d for d in seed.descriptors()]
        old = OncoLabIndex(descriptors, routes=seed.routes)
        institution = OncoLabInstitution(store, old, 'controlled-fixture')
        pin = institution.pin(); first = institution.index(pin).search_page('linear association', limit=8)
        assert refresh_reviewed_search_metadata(institution, seed) is not None
        current = institution.index()
        assert current.routes == old.routes
        assert institution.index(pin).describe('stat.scipy').purpose == 'Original generic numerical metadata'
        assert current.describe('stat.scipy').purpose == seed.describe('stat.scipy').purpose
        assert 'stat.scipy' in [c.capability_id for c in current.search_page('co movement linear association', limit=8).cards]
        with pytest.raises(ValueError, match='continuation'):
            current.search_page('linear association', limit=8, continuation=first.continuation)
        assert refresh_reviewed_search_metadata(institution, seed) is None
    finally: store.close()


async def _unqualified_dispatch_rejection():
    from pathlib import Path
    from types import SimpleNamespace
    from pydantic_ai import Agent
    from src.config.loader import load_models_config, load_runtime_config
    from src.config.models import RuntimeMode
    from src.persistence.repository import ResearchRepository
    from src.runtime.pydantic_ai.factory import build_harness_runtime
    from src.runtime.pydantic_ai.contracts import ResearcherDeps
    from src.runtime.pydantic_ai.scientific_tools import register_scientific_tools
    root = Path(__file__).resolve().parents[2]; store = SqliteResearchStore()
    runtime = build_harness_runtime(load_models_config(root / 'config/models.yaml'),
        load_runtime_config(root / 'config/runtime.yaml').model_copy(update={'mode': RuntimeMode.DETERMINISTIC}),
        repository=ResearchRepository(store))
    async def forbidden(*args, **kwargs): raise AssertionError('unqualified operation executed')
    runtime.execute_external = forbidden
    try:
        block = runtime.manager.allocate('Lung source assessment', 'dispatcher rejection check')
        runtime.repository.record_block(block)
        agent = Agent('test', deps_type=ResearcherDeps); register_scientific_tools(agent)
        function = agent._function_toolset.tools['run_reusable_method'].function
        ctx = SimpleNamespace(deps=ResearcherDeps(runtime, block.block_id))
        arguments = dict(capability_id='unqualified.method', acquisition_id='unknown', field='age', entity_field='id', unit='years', analysis_id='reject')
        with pytest.raises(ValueError, match='pinned reusable'): await function(ctx, **arguments)
        with pytest.raises(ValueError, match='no parameters'): await function(ctx, **arguments, parameters={'weights': [1]})
        assert not store.records(kind=RecordKind.MEASUREMENT) and not store.records(kind=RecordKind.EVIDENCE)
    finally: await runtime.gdc.aclose(); store.close()


def test_unqualified_dispatch_rejects_before_any_execution():
    import asyncio
    asyncio.run(_unqualified_dispatch_rejection())


def test_fixed_dispatch_does_not_execute_arbitrary_qualified_commands():
    from pathlib import Path
    from src.oncolab.reusable import supported_mean_operation
    store = SqliteResearchStore()
    try:
        candidate, _ = fixture(store)
        assert not supported_mean_operation(candidate)
        root = Path(__file__).resolve().parents[2]
        request = candidate.request.model_copy(update={'repository_url': 'https://github.com/TheAlgorithms/Python',
            'test_command': ('python', '-m', 'doctest', 'maths/average_mean.py'),
            'execute_command': ('python', str(root / 'src/science/reference_mean.py'), '/input/request.json')})
        fixed = candidate.model_copy(update={'request': request, 'receipt': candidate.receipt.model_copy(update={
            'repository_url': request.repository_url, 'commit_sha': '84b73d08f8bfa4e6bfae0243369c24f5a7539745'})})
        assert supported_mean_operation(fixed)
        assert not supported_mean_operation(fixed.model_copy(update={'request': request.model_copy(update={
            'execute_command': ('python', 'unqualified_driver.py')})}))
        assert not supported_mean_operation(fixed.model_copy(update={'receipt': fixed.receipt.model_copy(update={'commit_sha': 'b' * 40})}))
    finally: store.close()


@pytest.mark.parametrize("repetitions", [(0,), (0, 0, 0), (0, 1, 2)])
def test_utility_declared_repeats_cannot_replace_distinct_measured_rows(repetitions):
    """Adversarial synthetic reviews prove rejection only, never scientific utility."""
    from src.evals.reference import retain_utility_evaluation
    store = SqliteResearchStore()
    try:
        candidate, _ = fixture(store)
        corpus = content_hash({"fixture": "not independent scientific evidence"})
        observations = {"candidate_id": candidate.candidate_id, "scope_sha256": content_hash(SCOPE)}
        reviewer = store.append(StoredRecord(kind=RecordKind.SERVICE_EVENT, record_id="synthetic-negative-review", payload={
            "event_type": "IndependentUtilityReview", "observations_sha256": content_hash(observations),
            "corpus_sha256": corpus, "candidate_id": candidate.candidate_id, "scope_sha256": content_hash(SCOPE)}))
        report = {"mode": "live", "repeats": 3, "scientific_utility": 1, "corpus_sha256": corpus, "rows": [
            {"case_id": "adverse-fixture", "condition": "science_only", "memory_alternative_limit": 0,
             "repetition": repetition, "independent_review": "reviewed", "agreement": True,
             "observations": dict(observations), "review_reference": record_reference(reviewer)}
            for repetition in repetitions]}
        proof = retain_utility_evaluation(store, candidate.candidate_id, SCOPE, report, application_identity="fixture")
        assert proof.payload["status"] == ("passed" if repetitions == (0, 1, 2) else "unsupported")
        assert not store.records(kind=RecordKind.EVIDENCE)
    finally:
        store.close()
