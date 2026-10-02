"""Published-reference cases and neutral comparisons; labels never enter runtime."""
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from src.evals.harness import CONDITIONS, evaluate_condition
from src.persistence.records import RecordKind, StoredRecord
from src.provenance import content_hash


class ReferenceCase(BaseModel, frozen=True):
    model_config = ConfigDict(extra='forbid')
    case_id: str
    split: Literal['tuning', 'held_out']
    domain: str
    public_inputs: dict[str, Any]
    expected: dict[str, Any]
    reference_url: str
    label_basis: str
    independent_review: Literal['pending', 'reviewed'] = 'pending'
    reviewer_record: str | None = None


def load_reference_corpus(path):
    artifact = json.loads(Path(path).read_text())
    if artifact.get('version') != 'scientific-reference-corpus-v1': raise ValueError('unsupported reference corpus')
    cases = tuple(ReferenceCase.model_validate(row) for row in artifact['cases'])
    if len({case.case_id for case in cases}) != len(cases): raise ValueError('duplicate reference case')
    if any(case.independent_review == 'reviewed' and not case.reviewer_record for case in cases):
        raise ValueError('reviewed labels require an independent reviewer record')
    return cases


def evaluate_reference_cases(cases, adapter, *, models, policy, environment=None, repeats=1, agents_factory=None,
                             conditions=CONDITIONS, memory_alternatives=(0, 3), on_row=None):
    """Use the existing fresh-condition owner; adapters see public input only.

    The adapter calls real consumers and returns observations, not a winner.
    Semantic/stochastic adapters need at least three repetitions. Offline results
    explicitly remain contract measurements, never empirical semantic utility.
    """
    if not 1 <= repeats <= 20: raise ValueError('repeats must be 1..20')
    if policy.mode.value == 'live' and repeats < 3: raise ValueError('live comparisons require at least three repetitions')
    rows = []
    for case in cases:
        for condition in conditions:
            for alternative_limit in memory_alternatives:
                for repetition in range(repeats):
                    captured = {}
                    def runner(system, direction, repository, current_condition):
                        try:
                            captured.update(adapter(system, repository, current_condition,
                                json.loads(json.dumps(case.public_inputs)), alternative_limit=alternative_limit))
                        except Exception as error:
                            captured['adapter_error_type'] = type(error).__name__
                            captured['adapter_error_detail'] = str(error)[:1000]
                            raise
                        finally:
                            # Retain observed native receipts even when the adapter fails.
                            captured['native_semantic_receipts'] = [r.payload for r in repository.store.records(kind=RecordKind.JEV_CALL)]
                            captured['execution_receipts'] = [r.payload for r in repository.store.records(kind=RecordKind.LEDGER_EVENT)
                                if r.payload.get('event_type') in {'InstalledScienceResourceReceipt', 'ResourceAttempt', 'ReasonerFailure'}]
                            captured['usage'] = system.runtime.usage_summary()
                            captured['provider_cost'] = float(system.runtime.total_usage().cost) if system.runtime.total_usage().cost is not None else None
                            captured['downloaded_bytes'] = system.runtime.service_resources.downloaded_bytes

                    metrics = evaluate_condition(case.public_inputs.get('direction', 'Investigate lung cancer'), condition,
                        models=models, policy=policy, environment=environment, agents_factory=agents_factory, runner=runner)
                    captured['failure_type'] = metrics.error_type if metrics.status.value == 'failed' else None
                    comparable = {key: captured.get(key) for key in case.expected}
                    available = all(value is not None and value != 'unmeasured' for value in comparable.values())
                    rows.append({'case_id': case.case_id, 'split': case.split, 'domain': case.domain,
                        'condition': condition.value, 'memory_alternative_limit': alternative_limit, 'repetition': repetition,
                        'observations': captured, 'expected': case.expected, 'agreement': comparable == case.expected if available and metrics.status.value != 'failed' else None,
                        'metrics': metrics.model_dump(mode='json'), 'label_basis': case.label_basis,
                        'independent_review': case.independent_review, 'reference_url': case.reference_url})
                    if on_row is not None: on_row(rows[-1])
    return {'version': 'scientific-reference-comparison-v1', 'rows': rows, 'corpus_sha256': content_hash([case.model_dump(mode='json') for case in cases]),
        'effective_policy': policy.model_dump(mode='json'), 'models': models.model_dump(mode='json'), 'repeats': repeats,
        'mode': policy.mode.value, 'resource_comparability': 'same frozen policy and public inputs; observed costs may be unavailable',
        'scientific_utility': None, 'leakage_limits': ['Answer-bearing expected values, labels, split and reference URLs are withheld from adapters.',
            'Published cases may occur in model training; held-out split does not establish model pretraining independence.',
            'Independent scientific label review remains pending unless explicitly bound to a reviewer record.']}


def retain_utility_evaluation(store, candidate_id, scope, report, *, application_identity):
    """Candidate/scope-bound operational producer; unsupported utility cannot pass."""
    candidate = next((record for record in store.records(kind=RecordKind.SANDBOX_CANDIDATE) if record.record_id == candidate_id), None)
    if candidate is None or not scope or not report.get('rows'): raise ValueError('resolved candidate, scope and measured comparison required')
    relevant = [row for row in report['rows'] if row.get('observations', {}).get('candidate_id') == candidate_id
                and row.get('observations', {}).get('scope_sha256') == content_hash(scope)]
    if not relevant: raise ValueError('comparison does not resolve its measured candidate and scope')
    comparison = store.append(StoredRecord(kind=RecordKind.SERVICE_EVENT, record_id=content_hash(report),
        payload={'event_type': 'UtilityComparison', 'operational_only': True, 'comparison': report}))
    passed = (report.get('mode') == 'live' and report.get('repeats', 0) >= 3
        and all(row.get('independent_review') == 'reviewed' and row.get('agreement') is True for row in relevant)
        and report.get('scientific_utility') is not None)
    payload = {'version': 'candidate-utility-evaluation-v1', 'candidate_id': candidate_id,
        'candidate_sha256': content_hash(candidate.payload), 'scope_sha256': content_hash(scope),
        'application_identity': application_identity, 'status': 'passed' if passed else 'unsupported',
        'comparison_reference': {'seq': comparison.seq, 'record_id': comparison.record_id, 'sha256': content_hash(comparison.payload)},
        'scientific_utility': report.get('scientific_utility'), 'limitations': report.get('leakage_limits', [])}
    if passed and not utility_evaluation_resolves(store, payload, application_identity):
        payload['status'] = 'unsupported'
    return store.append(StoredRecord(kind=RecordKind.UTILITY_EVALUATION, record_id=content_hash(payload), payload=payload))


def utility_evaluation_resolves(store, payload, application_identity):
    """A passing label alone cannot qualify a method or its clinical usefulness."""
    from src.science.qualification import resolve_record
    try:
        if payload.get('version') != 'candidate-utility-evaluation-v1' or payload.get('status') != 'passed' or payload.get('application_identity') != application_identity:
            return False
        candidate = next(r for r in store.records(kind=RecordKind.SANDBOX_CANDIDATE) if r.record_id == payload['candidate_id'])
        if content_hash(candidate.payload) != payload['candidate_sha256']: return False
        reference = {**payload['comparison_reference'], 'kind': RecordKind.SERVICE_EVENT.value}
        comparison = resolve_record(store, reference, RecordKind.SERVICE_EVENT)
        if comparison.payload.get('event_type') != 'UtilityComparison': return False
        report = comparison.payload['comparison']
        relevant = [row for row in report['rows'] if row.get('observations', {}).get('candidate_id') == payload['candidate_id']
            and row.get('observations', {}).get('scope_sha256') == payload['scope_sha256']]
        if not relevant or report.get('mode') != 'live' or report.get('repeats', 0) < 3 or report.get('scientific_utility') is None:
            return False
        # The reviewer record must concern this comparison, rather than upstream
        # doctests or an unrelated published corpus annotation.
        for row in relevant:
            reviewer = resolve_record(store, row['review_reference'], RecordKind.SERVICE_EVENT)
            if (row.get('agreement') is not True or row.get('independent_review') != 'reviewed'
                or reviewer.payload.get('event_type') != 'IndependentUtilityReview'
                or reviewer.payload.get('observations_sha256') != content_hash(row.get('observations', {}))
                or reviewer.payload.get('corpus_sha256') != report.get('corpus_sha256')
                or reviewer.payload.get('candidate_id') != payload['candidate_id']
                or reviewer.payload.get('scope_sha256') != payload['scope_sha256']): return False
        return payload.get('scientific_utility') == report['scientific_utility']
    except (ValueError, KeyError, TypeError, StopIteration):
        return False


async def _reference_consumer_async(system, repository, condition, inputs, *, alternative_limit):
    """Fixed public-input operations through existing owners, with explicit unknowns."""
    import asyncio
    from src.block.models import CycleStatus
    from src.director.models import ResourceAllocation
    from src.runtime.pydantic_ai.semantic import measure_async
    from src.science.models import AnalysisSpec
    from src.sources.models import AcquisitionRecord
    from src.sources.representation import RepresentationNeed, assess_retained_representation
    runtime = system.runtime
    block = runtime.manager.create('Published reference method check in lung cancer mission', 'evaluation only', ResourceAllocation(seconds=240, handoff_reserve_seconds=30))
    repository.record_block(block)
    observed = {'scientific_utility': None, 'false_positive_rate': None, 'verified_replication': False}
    if runtime.enable_reasoner:
        from pydantic_ai.usage import RunUsage
        from src.runtime.pydantic_ai.contracts import ResearcherDeps
        from src.runtime.pydantic_ai.reasoner import BudgetedLiveReasoner
        runtime.claim(block.block_id, 'reasoner', runtime.max_reasoner_calls)
        if isinstance(runtime.reasoner, BudgetedLiveReasoner):
            usage = runtime.reasoner_usage.setdefault(block.block_id, RunUsage())
            proposal = await runtime.reasoner.generate(block.objective, json.dumps(inputs), usage=usage,
                usage_limits=runtime.usage_limits('reasoner'), deps=ResearcherDeps(runtime, block.block_id))
        else:
            proposal = await runtime.reasoner.generate(block.objective, json.dumps(inputs))
        runtime.append_event(block.block_id, 'ReasonerOutput', proposal.model_dump(mode='json'))
        observed['reasoner_used'] = True
    operation = inputs['operation']
    if operation == 'whole_lab':
        from src.evals.whole_lab import observe_whole_lab
        observed.update(await observe_whole_lab(system, repository, inputs, block, alternative_limit=alternative_limit))
    elif operation == 'numeric':
        spec = AnalysisSpec(analysis_id='reference', question=inputs.get('question', 'Published numerical reference'),
            population='reference fixture; not a lung cancer cohort', estimand=inputs['method'], method=inputs['method'],
            variables=tuple(inputs['values']), inputs=inputs['values'])
        try:
            result = await runtime.heavy_operation(block.block_id, runtime.science.execute, spec.model_copy(deep=True))
            repository.record_measurement(result, block.block_id)
            observed.update({key + '_rounded': round(result.values[key], 3) for key in inputs['observe']})
            observed['invalid_rejected'] = False
        except ValueError as error:
            observed.update(invalid_rejected=True, error_type=type(error).__name__)
    elif operation == 'representation':
        record = AcquisitionRecord.model_validate(inputs['acquisition'])
        runtime.retain_acquisition(block.block_id, record)
        checks = assess_retained_representation(record, RepresentationNeed.model_validate(inputs['need']))
        observed.update(eligible=checks['eligible'], availability=checks['availability'])
        if runtime.enable_jev:
            result = await measure_async(runtime, block.block_id, 'representation', record.acquisition_id,
                {'need': inputs['need'], 'representation': checks['representation'], 'checks': checks}, eligible=checks['eligible'])
            observed['semantic_action'] = result['frontier']['action']
    elif operation == 'statement':
        observed['source_support'] = 'unmeasured'
        if runtime.enable_jev:
            result = await measure_async(runtime, block.block_id, 'statement', content_hash(inputs),
                {'statement': inputs['statement'], 'epistemic_type': 'literature claim', 'resolved_support': inputs['resolved_support']})
            support = next((decision for decision in result['decisions'] if decision['question_id'].endswith(':support')), None)
            if support:
                observed['source_support'] = support['selected_option']
                observed['support_distribution'] = support['probabilities']
    elif operation == 'relation':
        if runtime.enable_jev:
            result = await measure_async(runtime, block.block_id, 'global_relation', 'reference-relation', inputs['relation'])
            observed['native_decisions'] = result['decisions']
        observed['scientific_resolution'] = 'unknown'
        # No deterministic classifier manufactures labels from statement wording.
        observed['relation_classification'] = 'unmeasured'
    elif operation == 'memory':
        from src.memory.models import CycleDigest, MemoryItem
        from src.memory.service import reference
        from src.runtime.pydantic_ai.search_tools import semantic_memory_context_async
        record = repository.store.append(StoredRecord(kind=RecordKind.SERVICE_EVENT, record_id='fixture-source-context',
            payload={'event_type': 'EvaluationContext', 'summary': inputs['retained_statement'], 'operational_only': True}))
        digest = CycleDigest(digest_id='reference-memory', cycle_id='previous-reference', mission_id=runtime.mission_id,
            direction=inputs['retained_statement'], recorded_at=record.recorded_at, cycle_status='incomplete', director_outcome='unknown',
            references=(reference(record),), uncertainties=(MemoryItem(item_id='unresolved', summary=inputs['retained_statement'],
                epistemic_status='uncertainty', references=(reference(record),)),))
        repository.store.append(StoredRecord(kind=RecordKind.MEMORY_DIGEST, record_id=digest.digest_id, payload=digest.model_dump(mode='json')))
        context = await semantic_memory_context_async(runtime, inputs['query'], block_id=block.block_id, alternative_limit=alternative_limit)
        observed['alternative_recalled'] = bool(context['digests'])
        observed['retrieval'] = context.get('retrieval')
    else:
        observed.update(status='unsupported_case_operation', operation=operation)
    repository.record_cycle(runtime.mission_id, system.mode.value, 'Lung cancer reference evaluation', (block.block_id,),
        status=CycleStatus.INCOMPLETE, error_type='ReferenceCheckOnly')
    observed['resources'] = runtime.resources(block.block_id)
    return observed


def reference_consumer_adapter(system, repository, condition, inputs, *, alternative_limit):
    # One event loop owns the entire condition, including governed execution.
    import asyncio
    return asyncio.run(_reference_consumer_async(system, repository, condition, inputs,
        alternative_limit=alternative_limit))
