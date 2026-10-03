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
    search_labels: dict[str, Any] = Field(default_factory=dict)


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
                        'independent_review': case.independent_review, 'reference_url': case.reference_url,
                        'search_metrics': search_metrics(captured, case.search_labels) if case.search_labels else None})
                    if on_row is not None: on_row(rows[-1])
    return {'version': 'scientific-reference-comparison-v1', 'rows': rows, 'corpus_sha256': content_hash([case.model_dump(mode='json') for case in cases]),
        'effective_policy': policy.model_dump(mode='json'), 'models': models.model_dump(mode='json'), 'repeats': repeats,
        'mode': policy.mode.value, 'resource_comparability': 'same frozen policy and public inputs; observed costs may be unavailable',
        'search_summary': summarize_search_rows(rows), 'scientific_utility': None, 'leakage_limits': ['Answer-bearing expected values, labels, split and reference URLs are withheld from adapters.',
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
        repeats = report.get('repeats')
        if (not relevant or report.get('mode') != 'live' or type(repeats) is not int
                or not 3 <= repeats <= 20 or report.get('scientific_utility') is None):
            return False
        # A declared count does not prove stochastic repetition. Each measured
        # candidate case/condition/memory series must contain every distinct row.
        series = {}
        for row in relevant:
            case_id, condition = row.get('case_id'), row.get('condition')
            memory, repetition = row.get('memory_alternative_limit'), row.get('repetition')
            if (not isinstance(case_id, str) or not case_id.strip()
                    or condition not in {value.value for value in CONDITIONS}
                    or type(memory) is not int or memory < 0
                    or type(repetition) is not int or not 0 <= repetition < repeats):
                return False
            seen = series.setdefault((case_id, condition, memory), set())
            if repetition in seen:
                return False
            seen.add(repetition)
            observed = row.get('observations', {})
            if observed.get('failure_type') is not None or observed.get('adapter_error_type') is not None:
                return False
        if any(seen != set(range(repeats)) for seen in series.values()):
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
    if inputs['operation'] == 'source_trajectory':
        from src.evals.whole_lab import observe_source_trajectory
        return await observe_source_trajectory(system, repository, inputs, alternative_limit=alternative_limit)
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
    if operation == 'search_comparison':
        observed.update(await observe_search_candidates(system, repository, inputs, block, alternative_limit=alternative_limit))
    elif operation == 'whole_lab':
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
    elif operation == 'fixed_projection':
        observed['fixed_payload_sha256'] = content_hash(inputs['payload'])
        if runtime.enable_jev:
            from src.director.frontier import GlobalFrontierPolicy
            policy = GlobalFrontierPolicy() if inputs['context_type'].startswith('global_') else None
            result = await measure_async(runtime, block.block_id, inputs['context_type'], inputs['identity'],
                inputs['payload'], eligible=inputs['eligible'], policy=policy)
            observed['fixed_action'] = result['frontier']['action']
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
            observed['relation_properties'] = {dimension: semantic_property(result['decisions'], dimension)
                for dimension in ('paraphrase', 'related_distinct', 'independent_replication', 'contradiction', 'resolvability')}
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


async def observe_search_candidates(system, repository, inputs, block, *, alternative_limit):
    """Matched public candidates through domain owners; evaluation labels stay outside."""
    from types import SimpleNamespace
    from src.memory.models import CycleDigest, MemoryItem
    from src.memory.service import reference
    from src.runtime.pydantic_ai.contracts import ResearcherDeps
    from src.runtime.pydantic_ai.search_tools import semantic_memory_context_async
    runtime = system.runtime
    domain = inputs['search_domain']
    candidates = inputs['candidates']
    observed = {'retrieved_ids': [], 'retained_ids': [], 'selectable_ids': [], 'merged_pairs': [],
        'duplicate_ids': [], 'fit_by_id': {}, 'merge_mode': 'no semantic merge operation; originals retained', 'choice_mode': 'fixed matched candidates; deterministic categorical ordering',
        'reasoner_influence': 'proposal observed separately; candidate set held fixed for marginal Jev comparison'}
    runtime.persist_state(runtime.research_state.start(block.block_id, block.objective))
    ctx = SimpleNamespace(deps=ResearcherDeps(runtime, block.block_id))
    # Invoke installed tool functions with the same runtime/deps as SDK dispatch.
    tools = system.agents.researcher._function_toolset.tools
    if domain in {'information', 'investigation'}:
        for candidate in candidates:
            record = repository.store.append(StoredRecord(kind=RecordKind.SERVICE_EVENT, record_id=candidate['id'],
                payload={'event_type': 'EvaluationContext', 'summary': candidate['summary'], 'operational_only': True}))
            item = MemoryItem(item_id=candidate['id'], summary=candidate['summary'], epistemic_status='uncertainty',
                references=(reference(record),), details=candidate.get('scope', {}))
            digest = CycleDigest(digest_id=candidate['id'], cycle_id=candidate['id'], mission_id=runtime.mission_id,
                direction=candidate['summary'], recorded_at=record.recorded_at, cycle_status='incomplete', director_outcome='unknown',
                references=(reference(record),), uncertainties=(item,))
            repository.store.append(StoredRecord(kind=RecordKind.MEMORY_DIGEST, record_id=digest.digest_id, payload=digest.model_dump(mode='json')))
        if domain == 'information':
            context = await semantic_memory_context_async(runtime, inputs['query'], limit=5, block_id=block.block_id,
                alternative_limit=alternative_limit)
            observed['retrieved_ids'] = [digest['digest_id'] for digest in context['digests']]
            observed['retained_ids'] = observed['retrieved_ids'][:]
            observed['selectable_ids'] = observed['retrieved_ids'][:]
            observed['retrieval'] = context['retrieval']
        else:
            from src.runtime.pydantic_ai.global_tools import prepare_frontier
            frontier = await prepare_frontier(runtime, inputs['query'], limit=10)
            aliases = {candidate.candidate_id: candidate.source_refs[0].record_id for candidate in frontier.candidates}
            observed['retrieved_ids'] = list(aliases.values())
            observed['retained_ids'] = list(aliases.values())
            observed['selectable_ids'] = [aliases[identity] for identity in frontier.beam]
            observed['frontier'] = frontier.model_dump(mode='json')
    elif domain == 'representation':
        from src.sources.models import AcquisitionRecord
        for candidate in candidates:
            record = AcquisitionRecord.model_validate(candidate['acquisition'])
            runtime.retain_acquisition(block.block_id, record)
        generated = await tools['generate_representation_candidates'].function(ctx, inputs['need'],
            [AcquisitionRecord.model_validate(candidate['acquisition']).acquisition_id for candidate in candidates])
        observed['generation'] = generated
        for candidate in candidates:
            record = AcquisitionRecord.model_validate(candidate['acquisition'])
            observed['retrieved_ids'].append(candidate['id']); observed['retained_ids'].append(candidate['id'])
            from src.sources.representation import RepresentationNeed, assess_retained_representation
            checks = assess_retained_representation(record, RepresentationNeed.model_validate(inputs['need']))
            action = 'keep_alive' if checks['eligible'] else 'defer'
            if runtime.enable_jev:
                result = await tools['assess_representation'].function(ctx, record.acquisition_id, inputs['need'])
                action = result['frontier']['action']
                observed['fit_by_id'][candidate['id']] = semantic_property(result['decisions'], 'sufficiency')
            if checks['eligible'] and action not in {'defer', 'reject_retain'}: observed['selectable_ids'].append(candidate['id'])
    elif domain == 'method':
        from src.sources.models import AcquisitionRecord
        record = AcquisitionRecord.model_validate(inputs['acquisition'])
        runtime.retain_acquisition(block.block_id, record)
        generated = await tools['generate_method_candidates'].function(ctx, inputs['need'], [record.acquisition_id], limit=8)
        observed['generation'] = generated
        from src.oncolab.methods import ScientificNeed, method_inputs, method_route_checks
        representations = method_inputs([record], ScientificNeed.model_validate(inputs['need']))
        for candidate in candidates:
            observed['retrieved_ids'].append(candidate['id']); observed['retained_ids'].append(candidate['id'])
            from src.oncolab.execution import check_routes
            index = runtime.index_for(block.block_id)
            checks = {'eligible': any(check['eligible'] for check in method_route_checks(index, candidate['id'], representations))}
            action = 'keep_alive' if checks['eligible'] else 'defer'
            if runtime.enable_jev:
                result = await tools['assess_method'].function(ctx, candidate['id'], inputs['need'], [record.acquisition_id])
                action = result['frontier']['action']
                observed['fit_by_id'][candidate['id']] = semantic_property(result['decisions'], 'estimand_fit')
            if checks['eligible'] and action not in {'defer', 'reject_retain'}: observed['selectable_ids'].append(candidate['id'])
    elif domain == 'hypothesis':
        for candidate in candidates:
            result = await tools['assess_hypothesis'].function(ctx, candidate['statement'], candidate['test'])
            observed['retrieved_ids'].append(candidate['id'])
            if result['exact_duplicate']: observed['duplicate_ids'].append(candidate['id'])
            # Exact duplicates remain source-linked; low fit is never a scientific negative.
            observed['retained_ids'].append(candidate['id'])
            if not result['exact_duplicate'] and result.get('frontier', {}).get('action') not in {'reject_retain', 'defer'}:
                observed['selectable_ids'].append(candidate['id'])
            if result.get('decisions'):
                observed['fit_by_id'][candidate['id']] = semantic_property(result['decisions'], 'test_alignment')
    else: raise ValueError('unsupported search domain')
    observed['selected_id'] = next(iter(observed['selectable_ids']), None)
    observed['preserved_count'] = len(set(observed['retained_ids']))
    observed['unknown_scientific_status'] = not repository.store.records(kind=RecordKind.EVIDENCE) and all(
        fragment.details.get('scientific_status') == 'unknown' for fragment in runtime.research_state.get(block.block_id).candidates
        if fragment.kind in {'hypothesis', 'hypothesis_transition'})
    return observed


def semantic_property(decisions, dimension):
    """Evaluation interpretation of a native Noul dimension, with an explicit unknown band."""
    value = next((decision['p_true'] for decision in decisions if decision['question_id'].endswith(':' + dimension)
                  and 'p_true' in decision), None)
    return None if value is None or .25 <= value <= .75 else value > .75


def search_metrics(observations, labels):
    """Labels enter only post-consumption scoring; missing denominators stay unknown."""
    useful = set(labels.get('useful_ids', ()))
    retrieved = set(observations.get('retrieved_ids', ()))
    retained = set(observations.get('retained_ids', ()))
    selectable = set(observations.get('selectable_ids', ()))
    duplicate = set(labels.get('duplicate_ids', ()))
    fits = labels.get('fit_by_id', {})
    measured = observations.get('fit_by_id', {})
    low_overlap = set(labels.get('low_overlap_ids', ()))
    relations = labels.get('relation_properties', {})
    relation_observed = observations.get('relation_properties', {})
    return {'useful_candidate_recall': len(useful & retrieved)/len(useful) if useful else None,
        'selectable_useful_recall': len(useful & selectable)/len(useful) if useful else None,
        'alternative_preservation': len(retrieved & retained)/len(retrieved) if retrieved else None,
        'false_semantic_merges': len(observations.get('merged_pairs', ())) if retrieved else None,
        'duplicate_work_avoidance': len(duplicate & set(observations.get('duplicate_ids', ())))/len(duplicate) if duplicate else None,
        'low_lexical_overlap_recall': len(low_overlap & retrieved)/len(low_overlap) if low_overlap else None,
        'fit_accuracy': sum(measured.get(identity) == expected for identity, expected in fits.items())/len(fits)
            if fits and all(measured.get(identity) is not None for identity in fits) else None,
        'next_investigation_alignment': observations.get('selected_id') in useful if useful and observations.get('selected_id') else None,
        'unknown_preserved': observations.get('unknown_scientific_status'),
        'relation_accuracy': sum(relation_observed.get(key) == value for key, value in relations.items())/len(relations)
            if relations and all(relation_observed.get(key) is not None for key in relations) else None,
        'scientific_utility': None}


def summarize_search_rows(rows):
    """Paired marginal deltas and instability; offline fixtures never imply empirical benefit."""
    from collections import defaultdict
    series = defaultdict(list)
    for row in rows:
        series[(row['case_id'], row['condition'], row['memory_alternative_limit'])].append(row)
    summaries = []
    for (case_id, condition, alternative_limit), values in series.items():
        signatures = []
        for row in values:
            receipts = row['observations'].get('native_semantic_receipts', ())
            # Compare semantic purposes/probabilities, excluding run-specific IDs/timing.
            signatures.append(content_hash([(receipt['context_type'], [(question['semantic_purpose'],
                {key: decision[key] for key in ('p_true', 'probabilities', 'expected_score', 'level_probabilities', 'confidence') if key in decision})
                for question in receipt.get('questions', ()) for decision in receipt.get('decisions', ())
                if question['question_id'] == decision['question_id']]) for receipt in receipts]))
        summaries.append({'case_id': case_id, 'condition': condition, 'memory_alternative_limit': alternative_limit,
            'metrics': [row.get('search_metrics') for row in values],
            'semantic_instability': len(set(signatures)) > 1 if len(values) > 1 and any(row['observations'].get('native_semantic_receipts') for row in values) else None,
            'policy_instability': len({content_hash({'selected': row['observations'].get('selected_id'), 'selectable': row['observations'].get('selectable_ids'), 'fit': row['observations'].get('fit_by_id')}) for row in values}) > 1 if len(values) > 1 else None,
            'failures': sum(row['observations'].get('failure_type') is not None for row in values),
            'provider_costs': [row['observations'].get('provider_cost') for row in values]})
    deltas = []
    for row in rows:
        baseline = {'science_jev': 'science_only', 'science_jev_reasoner': 'science_reasoner'}.get(row['condition'])
        if baseline is None or not row.get('search_metrics'): continue
        match = next((other for other in rows if other['case_id'] == row['case_id'] and other['condition'] == baseline
            and other['memory_alternative_limit'] == row['memory_alternative_limit'] and other['repetition'] == row['repetition']), None)
        if match is None: continue
        deltas.append({'case_id': row['case_id'], 'condition': row['condition'], 'baseline': baseline,
            'memory_alternative_limit': row['memory_alternative_limit'], 'repetition': row['repetition'],
            'metrics': {key: row['search_metrics'][key] - match['search_metrics'][key]
                if type(row['search_metrics'][key]) in {float, int} and type(match['search_metrics'][key]) in {float, int} else None
                for key in row['search_metrics']}})
    return {'series': summaries, 'marginal_jev_deltas': deltas,
        'interpretation': 'Generated labels measure contracts only. Fixed candidates isolate measurement; Reasoner proposals do not change this matched set. Unknown is not failure or scientific rejection.'}
