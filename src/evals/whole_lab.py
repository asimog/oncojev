"""Controlled multi-block adapter for the existing reference evaluation owner.

Scripted SDK choices test composition and lineage; they do not measure autonomous
clinical decision utility. Answer-bearing labels remain outside this adapter.
"""
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import FunctionModel
from src.block.models import BlockStatus, CycleStatus
from src.memory.service import ResearchMemory, reference
from src.persistence.records import RecordKind, StoredRecord
from src.researcher.state import StateFragment
from src.runtime.pydantic_ai.contracts import DirectorDeps, ResearcherDeps


def scripted_code(code, outputs=None):
    async def respond(messages, info):
        if not any(isinstance(message, ModelResponse) for message in messages):
            return ModelResponse(parts=[ToolCallPart('run_code', {'code': code}, tool_call_id='composition')])
        if outputs is not None:
            outputs.extend(str(part.content)[:6000] for message in messages for part in message.parts
                if getattr(part, 'part_kind', '') in {'tool-return', 'retry-prompt'})
        return ModelResponse(parts=[TextPart('Controlled composition returned; scientific utility remains unknown.')])
    return FunctionModel(respond)


async def observe_whole_lab(system, repository, inputs, block, *, alternative_limit):
    runtime = system.runtime; store = repository.store
    tool_outputs = []
    mission = store.append(StoredRecord(kind=RecordKind.MISSION, record_id=runtime.mission_id,
        payload={'direction': 'Investigate lung cancer through source-qualified designs; reference examples are numerical fixtures.'}))
    runtime.persist_state(runtime.research_state.start(block.block_id, block.objective))
    researcher = system.agents.fresh_researcher(block.block_id)
    code = ('p=await search_oncolab_page(query="co movement linear association", limit=8)\n'
        'r=await run_statistics(analysis_id="reference", question="Published numerical example; no oncology inference", '
        'estimand="reference correlation", method=' + repr(inputs['method']) + ', inputs=' + repr(inputs['values']) + ')\nr')
    with researcher.override(model=scripted_code(code, tool_outputs)):
        await researcher.run('Inspect published numerical reference through the existing tools', deps=ResearcherDeps(runtime, block.block_id))
    result = runtime.measurements[(block.block_id, 'reference')]
    runtime.persist_state(runtime.research_state.get(block.block_id).append('uncertainties', StateFragment(fragment_id='reference-scope',
        kind='uncertainty', summary='Reference association requires independent population/design qualification before oncology inference.',
        provenance=('reference',), details={'next_test': 'Qualify population and endpoint; do not infer clinical usefulness from a numerical example.'})))
    runtime.manager.finalize(block, BlockStatus.INTERRUPTED, 'Controlled evaluation handoff; no complete research trajectory claimed')
    repository.record_block(runtime.manager.block(block.block_id))
    # Same first-block inputs/work in both variants; withhold its cycle digest
    # until after the next choice to isolate access to prior experience.
    if alternative_limit:
        repository.record_cycle(runtime.mission_id, system.mode.value, 'Lung reference investigation', (block.block_id,),
            status=CycleStatus.INCOMPLETE, error_type='ControlledCompositionOnly', cycle_id=block.block_id)
        ResearchMemory(store).backfill()
    search_mode = inputs.get('search_mode', 'open_proposal')
    inspected = store.latest(RecordKind.INDEX_RECEIPT)
    proposal = {'objective': 'Qualify population and endpoint before clinical inference', 'proposed_test': 'Audit population and endpoint prerequisites',
        'population': 'Unqualified oncology population; retained numerical fixture is insufficient', 'design': 'Prerequisite assessment',
        'capability_ids': ['science.acquisition-summary'], 'context_refs': [reference(inspected).model_dump(mode='json')]}
    director_code = ('m=await read_research_memory(query="mechanistic vulnerability", mission_id=' + repr(runtime.mission_id) + ')\n'
        'review=await review_program(limit=5)\n'
        'f=await prepare_global_frontier(objective="mechanistic vulnerability", limit=5, proposals=' + repr([proposal] if search_mode == 'open_proposal' else []) + ')\n'
        'allowed=[c for c in f["candidates"] if c["candidate_id"] in f["beam"]]\n'
        'if allowed:\n c=allowed[0]\n b=await allocate_block(objective=c["objective"], why_now="controlled review-to-next-choice", frontier_id=f["frontier_id"], candidate_id=c["candidate_id"])\n'
        '{"memory":m,"review":review,"frontier":f}')
    with system.agents.director.override(model=scripted_code(director_code, tool_outputs)):
        await system.agents.director.run('Review prior work and choose the next scoped question', deps=DirectorDeps(runtime))
    allocations = [r for r in store.records(kind=RecordKind.LEDGER_EVENT) if r.payload.get('event_type') == 'DirectorBlockAllocated']
    if allocations:
        next_block = runtime.manager.blocks()[-1]
        next_researcher = system.agents.fresh_researcher(next_block.block_id)
        with next_researcher.override(model=scripted_code('s=await search_oncolab_page(query="survival inference", limit=8)\ns')):
            await next_researcher.run('Inspect availability; clinical validity remains unresolved', deps=ResearcherDeps(runtime, next_block.block_id))
    if not alternative_limit:
        repository.record_cycle(runtime.mission_id, system.mode.value, 'Lung reference investigation', (block.block_id,),
            status=CycleStatus.INCOMPLETE, error_type='ControlledCompositionOnly', cycle_id=block.block_id)
    reviews = store.records(kind=RecordKind.PROGRAM_REVIEW)
    frontier = store.latest(RecordKind.GLOBAL_FRONTIER)
    retrievals = store.records(kind=RecordKind.MEMORY_RETRIEVAL)
    return {**{key + '_rounded': round(result.values[key], 3) for key in inputs['observe']}, 'invalid_rejected': False,
        'memory_present': bool(alternative_limit), 'search_mode': search_mode, 'next_block_allocated': bool(allocations),
        'allocation_lineage': [r.payload for r in allocations], 'frontier': frontier.payload if frontier else None,
        'program_reviews': [r.payload for r in reviews], 'memory_retrievals': [r.payload for r in retrievals],
        'candidate_receipts': [r.payload for r in store.records(kind=RecordKind.INDEX_RECEIPT)],
        'blocks_observed': len(runtime.manager.blocks()), 'scientific_utility': None,
        'next_test_alignment': None, 'scientific_coverage': None, 'false_merges': None,
        'representation_fit': 'unmeasured', 'reusable_method_available': False,
        'tool_outputs': tool_outputs, 'choice_mode': 'scripted SDK/tool composition; autonomous usefulness unmeasured', 'verified_replication': False,
        'review_to_choice': bool(reviews and allocations), 'expected_scope': 'Published numerical references plus generated composition contracts; independent clinical review pending.'}
