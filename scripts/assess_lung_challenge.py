"""Explicit real-source alternative-model check; clinical interpretation unqualified."""
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

from pydantic_ai import Agent
from src.block.models import CycleStatus
from src.config.loader import load_models_config, load_runtime_config
from src.memory.service import ResearchMemory
from src.persistence.records import RecordKind
from src.persistence.repository import ResearchRepository
from src.persistence.store import SqliteResearchStore
from src.researcher.state import StateFragment
from src.runtime.pydantic_ai.contracts import ResearcherDeps
from src.runtime.pydantic_ai.factory import build_harness_runtime
from src.runtime.pydantic_ai.followup_tools import register_followup_tools
from src.runtime.pydantic_ai.scientific_tools import register_scientific_tools
from src.science.qualification import record_reference


async def main():
    root = Path(__file__).resolve().parents[1]
    runtime = build_harness_runtime(load_models_config(root / 'config/models.yaml'), load_runtime_config(root / 'config/runtime.yaml'))
    runtime.runtime_paths.data.mkdir(parents=True, exist_ok=True)
    store = SqliteResearchStore(runtime.runtime_paths.database())
    repository = ResearchRepository(store); runtime.repository = repository; runtime.mission_id = 'lung-challenge-assessment'
    block = runtime.manager.allocate('Lung clinical slice method-robustness assessment', 'Explicit source/uncertainty qualification', 300)
    repository.record_block(block)
    state = runtime.research_state.start(block.block_id, block.objective)
    runtime.persist_state(state.append('candidates', StateFragment(fragment_id='age-death-hypothesis', kind='hypothesis',
        summary='Negative standardized age/death-duration association in complete retained rows; exploratory only, no causal or survival inference.',
        provenance=('Predeclared scoped data/method check; clinical endpoint review pending',))))
    agent = Agent('test', deps_type=ResearcherDeps)
    register_scientific_tools(agent); register_followup_tools(agent)
    tools = agent._function_toolset.tools; ctx = SimpleNamespace(deps=ResearcherDeps(runtime, block.block_id))
    try:
        source = await runtime.gdc.search('cases', {'op': 'in', 'content': {'field': 'project.project_id', 'value': ['TCGA-LUAD', 'TCGA-LUSC']}},
            ('case_id', 'demographic.age_at_index', 'demographic.days_to_death', 'demographic.vital_status'), size=100)
        runtime.retain_acquisition(block.block_id, source)
        protocol = {'hypothesis_id': 'age-death-hypothesis', 'direction': 'negative', 'minimum_effect': .1, 'alpha': .05,
            'multiplicity_family': ['age-death-hypothesis', 'method-robustness']}
        population = 'Exactly retained TCGA-LUAD/LUSC UUID-ordered page with complete age/death-duration fields; not population coverage'
        estimand = 'Standardized bivariate association conditional on complete recorded death-duration rows'
        design = 'Exploratory independent-row model; unadjusted; endpoint, selection, confounding and representativeness unqualified'
        arguments = {'acquisition_id': source.acquisition_id, 'question': 'Inspect same-data alternative-model uncertainty; no survival estimate',
            'population': population, 'estimand': estimand, 'fields': {'x': 'demographic.age_at_index', 'y': 'demographic.days_to_death'},
            'entity_field': 'id', 'entity_unit': 'case', 'design': design, 'test_plan': protocol}
        baseline = await tools['run_source_analysis'].function(ctx, analysis_id='lung-age-death-baseline', method='pearson_correlation', **arguments)
        target = {'analysis_id': 'lung-age-death-alternative', 'question': arguments['question'], 'population': population, 'estimand': estimand,
            'method': 'ordinary_least_squares', 'variables': ['x', 'y'], 'fields': arguments['fields'], 'entity_field': 'id', 'entity_unit': 'case',
            'design': design, 'transformations': {'x': 'zscore', 'y': 'zscore'}, 'test_plan': protocol}
        declaration = await tools['declare_source_followup'].function(ctx, baseline_analysis_id='lung-age-death-baseline',
            comparison_id='method-robustness', kind='method_robustness', target_analysis=target, target_request=source.request,
            expected_discrimination='Point effects share scale; changed conditional-model intervals may expose assumption dependence. Same input is not replication.',
            alternative_explanations=['Clinical endpoint/time origin may be heterogeneous.', 'Complete death-duration records are selected; confounding and low information remain.', 'Fisher and OLS uncertainty assumptions differ.'])
        alternative = await tools['run_source_analysis'].function(ctx, analysis_id=target['analysis_id'], method=target['method'],
            transformations=target['transformations'], followup_id=declaration['followup_id'], **arguments)
        runtime.persist_state(runtime.research_state.get(block.block_id).append('uncertainties', StateFragment(fragment_id='endpoint-review-required',
            kind='uncertainty', summary='Require qualified endpoint/time-origin and selection design or a discriminating independent cohort before clinical interpretation.',
            provenance=(declaration['followup_id'],), details={'followup_id': declaration['followup_id'], 'next_test': 'Resolve endpoint and complete-case selection prerequisites; do not repeat the same-model observation as replication.'})))
        cycle = repository.record_cycle(runtime.mission_id, 'live', 'Lung cancer method-robustness qualification', (block.block_id,),
            status=CycleStatus.INCOMPLETE, error_type='ScientificReviewPending')
        memory = ResearchMemory(store); memory.backfill()
        contexts = memory.context('lung endpoint selection', limit=5, mission_id=runtime.mission_id).model_dump(mode='json')
        source_record = next(r for r in store.records(kind=RecordKind.ACQUISITION) if r.record_id == source.acquisition_id)
        result = next(r for r in store.records(kind=RecordKind.FOLLOWUP_RESULT) if r.record_id == declaration['followup_id'])
        output = root / 'var/task9-proof'; output.mkdir(exist_ok=True)
        report = {'database': str(runtime.runtime_paths.database()), 'source_reference': record_reference(source_record),
            'baseline': baseline, 'alternative': alternative, 'followup_reference': record_reference(result), 'followup': result.payload,
            'declaration': declaration, 'retained_context': contexts, 'scientific_utility': None,
            'limitations': ['Clinical challenge labels/interpretations remain independently unreviewed.', 'Same-data method comparison is not replication.',
                'Neither source coverage nor clinical survival validity is established.', 'No evidence was admitted by this qualification script.']}
        (output / 'lung-method-challenge.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'status': 'measured', 'complete_pairs': baseline['diagnostics']['counts']['complete_pairs'],
            'baseline_outcome': baseline['diagnostics']['hypothesis_test']['outcome'], 'challenge_outcome': result.payload['outcome'],
            'independence': result.payload['independence'], 'scientific_utility': None}), flush=True)
    finally:
        await runtime.gdc.aclose(); store.close()


if __name__ == '__main__': asyncio.run(main())
