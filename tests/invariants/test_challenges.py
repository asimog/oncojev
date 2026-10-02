"""Alternative-model invariants with published vectors; no clinical review claim."""
import json
from pathlib import Path
from uuid import UUID

import pytest

from src.provenance import ExecutionReference, content_hash
from src.science.execution import ScienceExecutor
from src.science.followup import FollowupPlan, compare_followup
from src.science.models import AnalysisSpec, HypothesisTestPlan, InvalidAnalysis
from src.sources.models import AcquisitionRecord, CoverageContract


def reference(values):
    return AcquisitionRecord(source='gdc', request={'fixture': True}, provenance=('controlled reference, not a real GDC response',),
        records=tuple({'id': str(UUID(int=i + 1)), 'case_id': str(UUID(int=i + 1)), 'x': x, 'y': y}
            for i, (x, y) in enumerate(zip(values['x'], values['y']))),
        coverage=CoverageContract(endpoint='cases', requested_size=len(values['x']), returned_rows=len(values['x']),
            reported_total=len(values['x']), complete=True, unique_entities=len(values['x']), ordering='fixture', id_field='id'))


def contract(acquisition):
    plan = HypothesisTestPlan(hypothesis_id='reference', direction='positive', minimum_effect=.1,
        multiplicity_family=('reference', 'method'))
    return AnalysisSpec(analysis_id='baseline', question='Numerical reference', population='published reference fixture',
        estimand='standardized bivariate association', method='pearson_correlation', variables=('x', 'y'), fields={'x': 'x', 'y': 'y'},
        entity_field='id', entity_unit='case', source_refs=(acquisition.acquisition_id,), test_plan=plan)


def test_standardized_ols_matches_independent_published_pearson_points_and_keeps_model_intervals():
    corpus = json.loads((Path(__file__).resolve().parents[2] / 'evals/reference/scientific-v1.json').read_text())
    cases = [case for case in corpus['cases'] if case['case_id'].startswith('anscombe-') and case['public_inputs']['operation'] == 'numeric']
    executor = ScienceExecutor()
    for case in cases:
        acquisition = reference(case['public_inputs']['values'])
        spec = contract(acquisition)
        baseline = executor.execute_source(acquisition, spec)
        alternative = spec.model_copy(update={'analysis_id': 'target', 'method': 'ordinary_least_squares',
            'transformations': {'x': 'zscore', 'y': 'zscore'}})
        target = executor.execute_source(acquisition, alternative)
        assert round(target.values['slope'], 3) == case['expected']['correlation_rounded']
        assert target.values['slope'] == pytest.approx(baseline.values['correlation'], abs=1e-12)
        assert all(value['ddof'] == 1 for value in target.diagnostics['standardization'].values())
        assert target.diagnostics['hypothesis_test']['uncertainty_method'] != baseline.diagnostics['hypothesis_test']['uncertainty_method']
        baseline_ref = ExecutionReference(kind='measurement', value='baseline', sha256=content_hash(baseline.model_dump(mode='json')), block_id='block')
        plan = FollowupPlan(followup_id='method', comparison_id='method', block_id='block', kind='method_robustness', baseline_attempt_id='baseline-attempt',
            baseline_measurement=baseline_ref, baseline_input=ExecutionReference(kind='acquisition', value=acquisition.acquisition_id,
                sha256=content_hash(acquisition.model_dump(mode='json')), block_id='block'), baseline_analysis=spec,
            target_analysis=alternative.model_copy(update={'source_refs': ()}), target_request=acquisition.request,
            expected_discrimination='Same point scale, model-dependent uncertainty; no independent replication.', alternative_explanations=('Model assumptions may differ.',))
        result = compare_followup(plan, baseline, target, acquisition, acquisition,
            ExecutionReference(kind='measurement', value='target', sha256=content_hash(target.model_dump(mode='json')), block_id='block'), confirmation_access='not_applicable')
        assert result.outcome in {'consistent', 'inconclusive'} and result.independence == 'overlap'
        assert result.outcome != 'replicated'
        with pytest.raises(ValueError, match='comparable'):
            FollowupPlan.model_validate({**plan.model_dump(mode='python'), 'target_analysis': alternative.model_copy(update={'source_refs': (), 'transformations': {}})})
        changed = acquisition.model_copy(update={'records': tuple({**row, 'y': -row['y']} for row in acquisition.records)})
        changed_target = executor.execute_source(changed, alternative.model_copy(update={'source_refs': (changed.acquisition_id,)}))
        rejected = compare_followup(plan, baseline, changed_target, acquisition, changed,
            ExecutionReference(kind='measurement', value='changed', sha256=content_hash(changed_target.model_dump(mode='json')), block_id='block'), confirmation_access='not_applicable')
        assert rejected.outcome == 'inconclusive' and 'changed data' in rejected.unresolved[0]


def test_standardization_rejects_constant_or_insufficient_complete_pairs():
    executor = ScienceExecutor()
    for values in ({'x': [1, 1, 1], 'y': [2, 3, 4]}, {'x': [1, 2], 'y': [2, 4]}):
        acquisition = reference(values)
        spec = contract(acquisition).model_copy(update={'method': 'ordinary_least_squares', 'transformations': {'x': 'zscore', 'y': 'zscore'}})
        with pytest.raises(InvalidAnalysis, match='enough complete nonconstant'):
            executor.execute_source(acquisition, spec)
