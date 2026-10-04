"""Candidate/scope-bound utility proof retention and qualification resolution.

Comparative observations are operational proof, never scientific evidence.
Evaluation producers and production governance share this existing OncoLab owner.
"""
from enum import StrEnum

from src.persistence.records import RecordKind, StoredRecord
from src.provenance import content_hash


class UtilityCondition(StrEnum):
    SCIENCE_ONLY = "science_only"
    SCIENCE_REASONER = "science_reasoner"
    SCIENCE_JEV = "science_jev"
    SCIENCE_JEV_REASONER = "science_jev_reasoner"


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
                    or condition not in {value.value for value in UtilityCondition}
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
