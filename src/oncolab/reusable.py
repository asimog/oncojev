"""Resolve block-pinned reusable authority from governed institutional history."""
from pathlib import Path
from src.persistence.records import RecordKind
from src.provenance import content_hash
from src.science.qualification import resolve_record, mean_scope_valid, scientific_qualification_resolves
from src.science.sandbox import SandboxMeasurementCandidate
from src.runtime.verification import local_verification_passed
from src.oncolab.utility import utility_evaluation_resolves


def supported_mean_operation(candidate):
    request = candidate.request
    root = Path(__file__).resolve().parents[2]
    return (request is not None and candidate.receipt.repository_url == 'https://github.com/TheAlgorithms/Python'
        and candidate.receipt.commit_sha == '84b73d08f8bfa4e6bfae0243369c24f5a7539745'
        and request.repository_url == candidate.receipt.repository_url
        and not request.dependency_wheels and not request.input_artifacts
        and request.install_command == ('python', '--version')
        and request.test_command == ('python', '-m', 'doctest', 'maths/average_mean.py')
        and request.execute_command == ('python', str(root / 'src/science/reference_mean.py'), '/input/request.json'))


def resolve_reusable_method(runtime, block_id, capability_id):
    index = runtime.index_for(block_id)
    descriptor = index.describe(capability_id)
    routes = index.routes.get(capability_id, ())
    if descriptor is None or len(routes) != 1 or descriptor.availability.value != 'reusable':
        raise ValueError('no qualified pinned reusable route')
    route = routes[0]
    if route.tool != 'run_reusable_method' or route.operation != 'finite_arithmetic_mean':
        raise ValueError('unsupported reusable operation')
    store = runtime.repository.store
    # A new block cannot inherit a historical route after its scoped retirement.
    current = runtime.institution.index()
    if route not in current.routes.get(capability_id, ()):
        raise ValueError('reusable operation retired or changed')
    revision = next(r for r in store.records(kind=RecordKind.REGISTRY_REVISION) if r.record_id == index.revision_id)
    accepted = False
    while revision is not None:
        review = store.record_at(revision.payload.get('governance_reference') or 0)
        if review is not None and review.kind == RecordKind.REGISTRY_REVIEW and review.payload.get('status') == 'accepted':
            proposal = next((r for r in store.records(kind=RecordKind.CAPABILITY_PROPOSAL) if r.record_id == review.payload.get('proposal_id')), None)
            if proposal is not None and proposal.payload.get('capability_id') == capability_id:
                accepted = (review.payload.get('scope_sha256') == route.scope_sha256
                    and route.model_dump(mode='json') in proposal.payload.get('routes', []))
                break
        revision = next((r for r in store.records(kind=RecordKind.REGISTRY_REVISION) if r.record_id == revision.payload.get('parent')), None)
    if not accepted: raise ValueError('accepted scoped registry review required')
    saved = next((r for r in store.records(kind=RecordKind.SANDBOX_CANDIDATE) if r.record_id == route.candidate_id), None)
    if saved is None: raise ValueError('unresolved route candidate')
    candidate = SandboxMeasurementCandidate.model_validate(saved.payload)
    if not supported_mean_operation(candidate): raise ValueError('unsupported fixed mean commands or source')
    if candidate.receipt.commit_sha != descriptor.version: raise ValueError('immutable software version mismatch')
    proofs = {}
    for kind in (RecordKind.REFERENCE_VALIDATION, RecordKind.ENVIRONMENT_QUALIFICATION, RecordKind.UTILITY_EVALUATION):
        matches = [r for r in store.records(kind=kind) if r.payload.get('candidate_id') == route.candidate_id
            and r.payload.get('scope_sha256') == route.scope_sha256]
        if not matches: raise ValueError('missing method qualification: ' + kind.value)
        proof = matches[-1]
        valid = (utility_evaluation_resolves(store, proof.payload, runtime.institution.application) if kind == RecordKind.UTILITY_EVALUATION
            else scientific_qualification_resolves(store, kind, proof.payload))
        if not valid: raise ValueError('unresolved or failed method qualification: ' + kind.value)
        proofs[kind] = proof
    declaration = resolve_record(store, proofs[RecordKind.REFERENCE_VALIDATION].payload['declaration_reference'], RecordKind.SERVICE_EVENT)
    scope = declaration.payload['scope']
    if not mean_scope_valid(scope) or content_hash(scope) != route.scope_sha256:
        raise ValueError('changed scientific scope')
    local = store.latest(RecordKind.LOCAL_VERIFICATION)
    if local is None or not local_verification_passed(local.payload, runtime.institution.application,
            environment_provider=runtime.verification_environment_provider, store=store):
        raise ValueError('current local execution qualification required')
    return candidate, proofs, scope
