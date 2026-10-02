"""Explicit ordinary open lung MAF acquisition and governed panel transform."""
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from pydantic_ai import Agent
from src.config.loader import load_models_config, load_runtime_config
from src.persistence.records import RecordKind, StoredRecord
from src.persistence.repository import ResearchRepository
from src.persistence.store import SqliteResearchStore
from src.runtime.pydantic_ai.factory import build_harness_runtime
from src.runtime.pydantic_ai.contracts import ResearcherDeps
from src.runtime.pydantic_ai.scientific_tools import register_scientific_tools
from src.science.qualification import record_reference
from src.sources.representation import RepresentationNeed, assess_retained_representation
from uuid import uuid4


async def main():
    root = Path(__file__).resolve().parents[1]
    runtime = build_harness_runtime(load_models_config(root / 'config/models.yaml'), load_runtime_config(root / 'config/runtime.yaml'))
    store = SqliteResearchStore(runtime.runtime_paths.database()); runtime.repository = ResearchRepository(store)
    block = runtime.manager.allocate('Lung mutation panel source readiness', 'Explicit compressed assay qualification', 300)
    runtime.repository.record_block(block)
    panel = ('TP53', 'EGFR', 'KRAS')
    declaration = store.append(StoredRecord(kind=RecordKind.SERVICE_EVENT, record_id=uuid4().hex, block_id=block.block_id,
        payload={'event_type': 'MutationPanelDeclared', 'operational_only': True, 'gene_symbols': panel,
            'scope': 'Exact observed masked variant events in selected source file; no mutation-free samples, clinical inference or burden.'}))
    agent = Agent('test', deps_type=ResearcherDeps); register_scientific_tools(agent)
    ctx = SimpleNamespace(deps=ResearcherDeps(runtime, block.block_id))
    try:
        files = await runtime.gdc.search('files', {'op': 'and', 'content': [
            {'op': 'in', 'content': {'field': 'cases.project.project_id', 'value': ['TCGA-LUAD', 'TCGA-LUSC']}},
            {'op': 'in', 'content': {'field': 'data_type', 'value': ['Masked Somatic Mutation']}},
            {'op': 'in', 'content': {'field': 'access', 'value': ['open']}}]},
            ('file_id', 'file_name', 'file_size', 'access', 'data_type', 'data_format', 'cases.case_id', 'cases.project.project_id'), size=5)
        runtime.retain_acquisition(block.block_id, files)
        selected = min(files.records, key=lambda row: row['file_size'])
        artifact = await runtime.gdc.acquire_file(selected['file_id'], block.block_id, 'gzip')
        runtime.repository.record_scientific_artifact(artifact)
        result = await agent._function_toolset.tools['transform_gdc_representation'].function(ctx,
            operation='parse_gdc_table', artifact_id=artifact.artifact_id, representation='mutation_events', gene_symbols=list(panel))
        parsed = runtime.resolve_acquisition(block.block_id, result['acquisition_id'])
        need = RepresentationNeed(estimand='Observed mutation-event coordinates', representation='mutation_events', entity_unit='mutation_event',
            entity_key='entity_id', fields={'position': 'start'}, numeric_roles=('position',), units={'position': 'base_1'})
        checks = assess_retained_representation(parsed, need)
        outcome = {'declaration_reference': record_reference(declaration), 'file_selection': selected,
            'artifact_reference': record_reference(next(r for r in store.records(kind=RecordKind.SCIENTIFIC_ARTIFACT) if r.record_id == artifact.artifact_id)),
            'transform_reference': record_reference(next(r for r in store.records(kind=RecordKind.REPRESENTATION_PARSE) if r.record_id == parsed.acquisition_id)),
            'source_rows': parsed.coverage.reported_total, 'selected_rows': len(parsed.records), 'selection': parsed.request['selection'],
            'readiness': checks, 'downloaded_data_bytes': runtime.service_resources.data_downloaded_bytes, 'receipt': result['receipt'],
            'database': str(runtime.runtime_paths.database()), 'scientific_utility': None,
            'limitations': ['Exact mutation-event readiness only; sample/case links and callable territory remain separate prerequisites.',
                'Independent clinical interpretation review remains pending.', 'No evidence or mutation absence admitted.']}
        output = root / 'var/task5-proof'; output.mkdir(exist_ok=True)
        (output / 'lung-maf-panel.json').write_text(json.dumps(outcome, indent=2) + '\n')
        print(json.dumps({'status': 'parsed', 'source_rows': outcome['source_rows'], 'selected_rows': outcome['selected_rows'],
            'ready': checks['eligible'], 'compressed_bytes': artifact.size_bytes, 'decoded_bytes': outcome['selection']['decoded_bytes']}), flush=True)
    finally: await runtime.gdc.aclose(); store.close()


if __name__ == '__main__': asyncio.run(main())
