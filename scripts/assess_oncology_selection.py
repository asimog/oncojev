"""Explicit source-bound assessment of the frozen three-tool lung selection."""
import asyncio
import json
from pathlib import Path
from uuid import uuid4

from src.config.loader import load_models_config, load_runtime_config
from src.persistence.records import RecordKind, StoredRecord
from src.persistence.repository import ResearchRepository
from src.persistence.store import SqliteResearchStore
from src.runtime.pydantic_ai.factory import build_harness_runtime
from src.science.qualification import record_reference
from src.science.representation import derive_gdc_clinical

SELECTION = ('lung.age-slice-summary', 'lung.overall-survival', 'lung.tmb')


async def main():
    root = Path(__file__).resolve().parents[1]
    runtime = build_harness_runtime(load_models_config(root / 'config/models.yaml'), load_runtime_config(root / 'config/runtime.yaml'))
    runtime.runtime_paths.data.mkdir(parents=True, exist_ok=True)
    store = SqliteResearchStore(runtime.runtime_paths.database())
    runtime.repository = ResearchRepository(store)
    block = runtime.manager.allocate('Assess frozen lung oncology selection', 'Explicit prerequisites and existing-tool baseline', 300)
    runtime.repository.record_block(block)
    declaration = store.append(StoredRecord(kind=RecordKind.SERVICE_EVENT, record_id=uuid4().hex, block_id=block.block_id,
        payload={'event_type': 'OncologySelectionDeclared', 'version': 'lung-selection-v1', 'tools': SELECTION,
            'need': 'Source-bound descriptive age, survival availability and mutation-burden prerequisites',
            'policy': 'No imputation or inferred denominator; no inference without endpoint/design qualification',
            'operational_only': True}))
    try:
        filters = {'op': 'in', 'content': {'field': 'project.project_id', 'value': ['TCGA-LUAD', 'TCGA-LUSC']}}
        cases = await runtime.gdc.search('cases', filters, ('case_id', 'project.project_id', 'demographic.age_at_index',
            'demographic.vital_status', 'demographic.days_to_death', 'diagnoses.age_at_diagnosis', 'diagnoses.days_to_last_follow_up'), size=100)
        runtime.retain_acquisition(block.block_id, cases)
        source = next(r for r in store.records(kind=RecordKind.ACQUISITION) if r.record_id == cases.acquisition_id)
        baseline = await runtime.heavy_operation(block.block_id, runtime.science.measure_acquisition, cases, 'lung-age-existing-summary', 'demographic.age_at_index')
        measurement = runtime.repository.record_measurement(baseline, block.block_id)
        survival, transform = await runtime.heavy_operation(block.block_id, derive_gdc_clinical, cases, block.block_id, 'survival')
        runtime.retain_acquisition(block.block_id, survival)
        transformed = runtime.repository.record_immutable(RecordKind.REPRESENTATION_PARSE, survival.acquisition_id, transform, block.block_id)
        mutations = await runtime.gdc.search('files', {'op': 'and', 'content': [
            {'op': 'in', 'content': {'field': 'cases.project.project_id', 'value': ['TCGA-LUAD', 'TCGA-LUSC']}},
            {'op': 'in', 'content': {'field': 'data_type', 'value': ['Masked Somatic Mutation']}}]},
            ('file_id', 'access', 'data_format', 'data_type', 'file_size', 'cases.case_id', 'cases.project.project_id'), size=5)
        runtime.retain_acquisition(block.block_id, mutations)
        mutation_source = next(r for r in store.records(kind=RecordKind.ACQUISITION) if r.record_id == mutations.acquisition_id)
        decisions = [
            {'tool': SELECTION[0], 'decision': 'no_build', 'reason': 'adequate_existing_tool', 'existing_capability': 'science.acquisition-summary',
             'source_reference': record_reference(source), 'baseline_reference': record_reference(measurement),
             'observed': baseline.values, 'scientific_scope': 'Descriptive exact retained slice only; no population or clinical inference.'},
            {'tool': SELECTION[1], 'decision': 'no_build', 'reason': 'unavailable_validated_endpoint_and_censoring_design',
             'source_reference': record_reference(source), 'transform_reference': record_reference(transformed),
             'observed': {'retained_cases': len(cases.records), 'complete_time_event_rows': sum(row['time_days'] is not None and row['event'] is not None for row in survival.records)},
             'missing_prerequisites': ['Common audited time origin', 'Qualified event/censoring assumptions', 'Prespecified estimand/covariates and missingness design'],
             'scientific_scope': 'Availability inspection only; no survival estimate or absence claim.'},
            {'tool': SELECTION[2], 'decision': 'no_build', 'reason': 'unavailable_source_bound_callable_territory',
             'source_reference': record_reference(mutation_source), 'observed': {'metadata_files': len(mutations.records), 'formats': sorted({row.get('data_format', 'unknown') for row in mutations.records})},
             'missing_prerequisites': ['Exact eligible callable territory in Mb', 'Audited sample/aliquot/build/assay linkage and variant denominator'],
             'scientific_scope': 'Mutation listings/variants cannot establish TMB; no burden estimate.'}]
        outcome = store.append(StoredRecord(kind=RecordKind.SERVICE_EVENT, record_id=uuid4().hex, block_id=block.block_id,
            payload={'event_type': 'OncologySelectionAssessed', 'operational_only': True, 'declaration_reference': record_reference(declaration),
                'decisions': decisions, 'scientific_utility': None, 'independent_review': 'broader scientific labels remain pending'}))
        output = root / 'var/task8-proof'; output.mkdir(exist_ok=True)
        report = {'database': str(runtime.runtime_paths.database()), 'block_id': block.block_id, 'selection': SELECTION,
            'outcome_reference': record_reference(outcome), 'decisions': decisions, 'downloaded_data_bytes': runtime.service_resources.data_downloaded_bytes,
            'coverage': cases.coverage.model_dump(mode='json'), 'testing': runtime.runtime_paths.testing}
        (output / 'lung-selection.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'status': 'assessed', 'decisions': [(row['tool'], row['decision'], row['reason']) for row in decisions],
            'downloaded_data_bytes': report['downloaded_data_bytes']}), flush=True)
    finally:
        await runtime.gdc.aclose(); store.close()


if __name__ == '__main__': asyncio.run(main())
