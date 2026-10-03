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


async def observe_source_trajectory(system, repository, inputs, *, alternative_limit):
    """Controlled source replay through actual role tools, semantic frontier and Science.

    Scientific outcomes drive the branch. Scripted choices qualify lineage only;
    historical-source replay does not qualify fresh acquisition or clinical utility.
    """
    from src.sources.models import AcquisitionRecord
    from src.persistence.reconstruct import reconstruct_block
    runtime = system.runtime; store = repository.store; outputs = []
    acquisition = AcquisitionRecord.model_validate(inputs['acquisition'])
    from src.provenance import content_hash
    if inputs['source_replay_basis'].get('payload_sha256') != content_hash(acquisition.model_dump(mode='json')):
        raise ValueError('retained source replay payload does not match its declared basis')
    source = store.append(StoredRecord(kind=RecordKind.ACQUISITION, record_id=acquisition.acquisition_id,
        payload=acquisition.model_dump(mode='json')))
    store.append(StoredRecord(kind=RecordKind.MISSION, record_id=runtime.mission_id,
        payload={'direction': 'Assess limitations of a retained lung GDC source slice; no survival or causal claim.'}))
    runtime.cycle_id = 'source-trajectory-first'
    objective = 'Measure an exploratory age versus recorded death-duration association in the retained lung source slice'
    proposal = {'objective': objective, 'proposed_test': 'Pearson directional effect-bound comparison on complete source case rows',
        'population': 'Retained public lung cases response slice only', 'design': 'exploratory complete-pair association; endpoint validity unknown',
        'capability_ids': ['science.source-paired'], 'context_refs': [reference(source).model_dump(mode='json')]}
    alternative = {**proposal, 'objective': 'Inspect missingness before association', 'proposed_test': 'source field coverage summary',
        'capability_ids': ['science.acquisition-summary']}
    async def allocate(proposals, selected_objective, why):
        code = ('f=await prepare_global_frontier(objective="lung source slice limitations", limit=3, proposals=' + repr(proposals) + ')\n'
            'choices=[c for c in f["candidates"] if c["objective"]==' + repr(selected_objective) + ' and c["candidate_id"] in f["beam"]]\n'
            'assert choices, "semantic frontier retained proposal outside selectable beam"\n'
            'c=choices[0]\n'
            'b=await allocate_block(objective=c["objective"], why_now=' + repr(why) + ', frontier_id=f["frontier_id"], candidate_id=c["candidate_id"])\nb')
        count = len(runtime.manager.blocks())
        with system.agents.director.override(model=scripted_code(code, outputs)):
            await system.agents.director.run('Choose a source-grounded investigation', deps=DirectorDeps(runtime))
        if len(runtime.manager.blocks()) != count + 1: raise ValueError('source trajectory allocation failed')
        return runtime.manager.blocks()[-1]
    first = await allocate([proposal, alternative], objective, 'Retained input uncertainty; compare association with coverage alternative')
    from uuid import uuid4
    first_input = acquisition.model_copy(update={'acquisition_id': str(uuid4())}, deep=True)
    runtime.retain_acquisition(first.block_id, first_input)
    researcher = system.agents.fresh_researcher(first.block_id)
    code = ('h=await assess_hypothesis(hypothesis="Age has a positive association with raw recorded death duration in the retained slice", '
        'proposed_test="exploratory Pearson directional effect-bound comparison")\n'
        'r=await run_source_analysis(acquisition_id=' + repr(first_input.acquisition_id) + ', analysis_id="source-association", '
        'question="Raw field association; no censoring-aware survival claim", population="retained public lung case rows", '
        'estimand="complete-pair Pearson correlation", method="pearson_correlation", '
        'fields={"x":"demographic.age_at_index","y":"demographic.days_to_death"}, entity_field="id", entity_unit="case", '
        'design="exploratory complete-pair association; independence/model assumptions unverified", '
        'test_plan={"hypothesis_id":h["identity"],"direction":"positive","minimum_effect":0.3,"multiplicity_family":[h["identity"]]})\nr')
    async def execute_owned(agent, block, code):
        runtime.researcher_factory = lambda _block_id: agent
        with agent.override(model=scripted_code(code, outputs)):
            with system.agents.director.override(model=scripted_code('await launch_researcher(block_id=' + repr(block.block_id) + ')', outputs)):
                await system.agents.director.run('Launch the owned fresh Researcher', deps=DirectorDeps(runtime))
            if runtime.active_research is None: raise ValueError('owned Researcher was not launched')
            await runtime.active_research.task
            if runtime.active_research.error is not None: raise runtime.active_research.error
    await execute_owned(researcher, first, code)
    result = runtime.measurements.get((first.block_id, 'source-association'))
    if result is None: raise ValueError('source trajectory measurement unavailable: ' + repr(outputs[-1:])[-500:])
    outcome = result.diagnostics['hypothesis_test']['outcome']
    attempt = store.latest(RecordKind.SCIENTIFIC_ATTEMPT, block_id=first.block_id)
    repository.record_cycle(runtime.mission_id, system.mode.value, 'Lung source limitation test', (first.block_id,),
        status=CycleStatus.COMPLETE, cycle_id=runtime.cycle_id)
    memory = ResearchMemory(store); memory.backfill()
    first_digest_ids = [digest.digest_id for digest in memory.digests()]
    # Observable deterministic branch, never a benchmark label or semantic claim.
    next_objective = ('Inspect missingness and endpoint prerequisites before interpreting the inconclusive raw-field association'
        if outcome == 'inconclusive' else 'Inspect independent-cohort prerequisites before interpreting the exploratory association')
    next_proposal = {'objective': next_objective, 'proposed_test': 'Descriptive coverage of raw recorded duration; endpoint/censoring validity remains unknown',
        'population': 'same retained public response slice; no independent replication', 'design': 'source-field validity prerequisite assessment',
        'capability_ids': ['science.acquisition-summary'], 'context_refs': [reference(attempt).model_dump(mode='json')],
        'prerequisite_refs': [reference(source).model_dump(mode='json')]}
    runtime.cycle_id = 'source-trajectory-next'
    second = await allocate([next_proposal], next_objective, f'Prior source test outcome={outcome}; inspect information/design limits before another association')
    second_input = acquisition.model_copy(update={'acquisition_id': str(uuid4())}, deep=True)
    runtime.retain_acquisition(second.block_id, second_input)
    second_researcher = system.agents.fresh_researcher(second.block_id)
    code = ('r=await measure_acquisition(acquisition_id=' + repr(second_input.acquisition_id) + ',analysis_id="duration-coverage", '
        'numeric_field="demographic.days_to_death")\nr')
    await execute_owned(second_researcher, second, code)
    if (second.block_id, 'duration-coverage') not in runtime.measurements: raise ValueError('next source prerequisite measurement unavailable')
    repository.record_cycle(runtime.mission_id, system.mode.value, 'Lung source prerequisite assessment', (second.block_id,),
        status=CycleStatus.COMPLETE, cycle_id=runtime.cycle_id)
    memory.backfill()
    allocations = [record for record in store.records(kind=RecordKind.LEDGER_EVENT) if record.payload['event_type'] == 'DirectorBlockAllocated']
    return {'scientific_utility': None, 'source_replay_basis': inputs['source_replay_basis'],
        'choice_mode': 'scripted actual SDK roles; deterministic outcome branch; autonomous utility unmeasured',
        'source_outcome': outcome, 'source_measurement': result.model_dump(mode='json'),
        'changed_next_objective': second.objective != first.objective, 'next_choice_reason': next_objective,
        'allocation_lineage': [record.model_dump(mode='json') for record in allocations],
        'initial_digest_ids': first_digest_ids, 'final_digest_ids': [digest.digest_id for digest in memory.digests()],
        'reconstruction': [reconstruct_block(store, block.block_id).model_dump(mode='json') for block in (first, second)],
        'trajectory_records': [record.model_dump(mode='json') for record in store.records()], 'tool_outputs': outputs,
        'verified_replication': False, 'endpoint_validity': 'unknown', 'fresh_acquisition': False,
        'closure_scope': 'actual owned Researcher completion/dossier/Delta; scripted choices do not qualify autonomous scientific utility'}
