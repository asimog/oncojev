"""Real source use followed by honest promotion rejection; no invented utility."""
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
from pydantic_ai import Agent
from src.config.loader import load_models_config, load_runtime_config
from src.persistence.records import RecordKind
from src.persistence.repository import ResearchRepository
from src.persistence.store import SqliteResearchStore
from src.runtime.pydantic_ai.factory import build_harness_runtime
from src.runtime.pydantic_ai.contracts import ResearcherDeps, register_researcher_tools
from src.science.qualification import record_reference, recover_environment_inputs
from src.memory.service import reference
from src.oncolab.governance import CapabilityProposal, propose, review
from src.oncolab.execution import ExecutionRoute
from src.oncolab.models import OncoLabAvailability, OncoLabValidationState
from src.oncolab.utility import retain_utility_evaluation
from src.provenance import content_hash


async def main():
    root = Path(__file__).resolve().parents[1]
    ref = json.loads((root / 'var/task6-proof/reference-qualification-corrected.json').read_text())
    env = json.loads((root / 'var/task7-proof/environment-qualification-complete.json').read_text())
    store = SqliteResearchStore(ref['database']); repository = ResearchRepository(store)
    runtime = build_harness_runtime(load_models_config(root / 'config/models.yaml'), load_runtime_config(root / 'config/runtime.yaml'), repository=repository)
    original, inputs = recover_environment_inputs(store, env['lock_reference'], runtime_identity=env['qualification']['runtime_identity'])
    agent = Agent('test', deps_type=ResearcherDeps); register_researcher_tools(agent)
    tools = agent._function_toolset.tools; admitted = []; uses = []; fresh_records = []
    try:
        for project in ('TCGA-LUAD', 'TCGA-LUSC'):
            block = runtime.manager.allocate('Retained lung age mean: ' + project, 'explicit distinct source-use qualification', 300)
            repository.record_block(block); runtime.persist_state(runtime.research_state.start(block.block_id, block.objective))
            source = await runtime.gdc.search('cases', {'op': 'in', 'content': {'field': 'project.project_id', 'value': [project]}}, ('case_id', 'demographic.age_at_index'), size=20)
            runtime.retain_acquisition(block.block_id, source)
            rows = [row for row in source.records if isinstance(row.get('demographic', {}).get('age_at_index'), (int, float))]
            if not rows: raise RuntimeError('no finite recorded ages')
            values = [row['demographic']['age_at_index'] for row in rows]
            candidate = await runtime.execute_external(block.block_id, original.request.model_copy(update={'requested_ref': original.receipt.commit_sha, 'input_json': {'values': values}}), recovery_inputs=inputs)
            ctx = SimpleNamespace(deps=ResearcherDeps(runtime, block.block_id)); analysis = uuid4().hex
            measured = await tools['validate_sandbox_measurement'].function(ctx, candidate_id=candidate.candidate_id, analysis_id=analysis)
            # Explicit source lineage accompanies the replay-validated result.
            result = runtime.measurements[(block.block_id, analysis)].model_copy(update={'source_refs': (candidate.candidate_id, source.acquisition_id),
                'diagnostics': {'source_acquisition': source.acquisition_id, 'source_sha256': source.content_sha256,
                    'field': 'demographic.age_at_index', 'included_entities': [r['id'] for r in rows],
                    'included_rows': len(rows), 'excluded_missing_rows': len(source.records) - len(rows)},
                'limitations': ('Descriptive recorded age slice; source coverage and missingness may be selective. No clinical inference.',)})
            runtime.measurements[(block.block_id, analysis)] = result
            runtime.persist_state(runtime.research_state.get(block.block_id).add_measurement(result)); repository.record_measurement(result, block.block_id)
            evidence = await tools['admit_measurement'].function(ctx, analysis_id=analysis)
            fresh_records.append(next(r for r in store.records(kind=RecordKind.SANDBOX_CANDIDATE) if r.record_id == candidate.candidate_id))
            admitted.extend(r for r in store.records(block_id=block.block_id) if r.kind in {RecordKind.MEASUREMENT, RecordKind.EVIDENCE})
            uses.append({'project': project, 'block_id': block.block_id, 'source_reference': record_reference(next(r for r in store.records(kind=RecordKind.ACQUISITION) if r.record_id == source.acquisition_id)), 'measurement': result.model_dump(mode='json'), 'evidence_id': evidence['evidence_id']})
            print(json.dumps({'project': project, 'included': len(rows), 'mean': measured['values']['mean']}), flush=True)
        utility = retain_utility_evaluation(store, original.candidate_id, ref['scope'], {'mode': 'live', 'repeats': 3, 'rows': [
            {'observations': {'candidate_id': original.candidate_id, 'scope_sha256': content_hash(ref['scope'])}, 'agreement': None,
             'independent_review': 'pending'}], 'scientific_utility': None, 'leakage_limits': ['Independent scientific utility review unavailable.']}, application_identity=runtime.institution.application)
        supporting = [next(r for r in store.records(kind=RecordKind.SANDBOX_CANDIDATE) if r.record_id == original.candidate_id), *fresh_records, *admitted,
            store.record_at(ref['reference_validation']['seq']), store.record_at(env['qualification_reference']['seq']), utility,
            store.latest(RecordKind.LOCAL_VERIFICATION), next(r for r in store.records(kind=RecordKind.EXTERNAL_LOOKUP)
                if any(c.get('homepage') == original.receipt.repository_url and c.get('metadata', {}).get('commit_sha') == original.receipt.commit_sha for c in r.payload.get('cards', [])))]
        descriptor = runtime.institution.index().describe('software.github-scientific').model_copy(update={
            'capability_id': 'method.lung-retained-mean', 'name': 'Pinned finite retained mean', 'purpose': 'Descriptive retained numeric slice',
            'implementation_or_source': original.receipt.repository_url, 'version': original.receipt.commit_sha,
            'availability': OncoLabAvailability.REUSABLE, 'validation_state': OncoLabValidationState.REUSABLE})
        proposal = CapabilityProposal(capability_id=descriptor.capability_id, transition='promotion', parent=runtime.institution.pin().oncolab_registry_revision,
            descriptor=descriptor, scope=ref['scope'], routes=(ExecutionRoute(tool='run_reusable_method', operation='finite_arithmetic_mean', candidate_id=original.candidate_id, scope_sha256=content_hash(ref['scope'])),),
            references=tuple(reference(r) for r in supporting if r is not None), rationale='Assess repeated actual lung source use; independent utility remains unmeasured.')
        saved = propose(runtime.institution, proposal); outcome = review(runtime.institution, saved.record_id)
        assert outcome['status'] == 'rejected' and any('utility' in reason for reason in outcome['reasons'])
        output = root / 'var/task10-proof'; output.mkdir(exist_ok=True)
        (output / 'reusable-mean.json').write_text(json.dumps({'database': ref['database'], 'uses': uses, 'proposal_id': proposal.proposal_id,
            'review': outcome, 'utility_reference': record_reference(utility), 'scientific_utility': None,
            'accepted_reusable_execution': False, 'limitations': ['Repeated source use is operational evidence, not reviewed scientific utility.',
                'No accepted reusable route was fabricated. Native acceptance/update/retirement proof remains blocked.']}, indent=2) + '\n')
        print(json.dumps(outcome), flush=True)
    finally: await runtime.gdc.aclose(); store.close()


if __name__ == '__main__': asyncio.run(main())
