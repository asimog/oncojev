"""Reopen actual challenge history and retain a scripted, source-grounded next choice."""
import asyncio
import json
from pathlib import Path

from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import FunctionModel
from src.config.loader import load_models_config, load_runtime_config
from src.memory.service import reference
from src.persistence.records import RecordKind, StoredRecord
from src.persistence.repository import ResearchRepository
from src.persistence.store import SqliteResearchStore
from src.runtime.pydantic_ai.agents import create_agents
from src.runtime.pydantic_ai.contracts import DirectorDeps
from src.runtime.pydantic_ai.factory import build_harness_runtime


async def main():
    root = Path(__file__).resolve().parents[1]
    report = json.loads((root / 'var/task9-proof/lung-method-challenge.json').read_text())
    store = SqliteResearchStore(report['database'])
    runtime = build_harness_runtime(load_models_config(root / 'config/models.yaml'), load_runtime_config(root / 'config/runtime.yaml'),
        repository=ResearchRepository(store))
    runtime.mission_id = 'lung-challenge-assessment'; runtime.enable_jev = False; runtime.enable_reasoner = False
    if not any(r.record_id == runtime.mission_id for r in store.records(kind=RecordKind.MISSION)):
        store.append(StoredRecord(kind=RecordKind.MISSION, record_id=runtime.mission_id, payload={'direction': 'Investigate lung cancer; preserve clinical and source uncertainty'}))
    result = store.record_at(report['followup_reference']['seq'])
    context = reference(result).model_dump(mode='json')
    proposal = {'objective': 'Qualify lung endpoint and complete-case selection before clinical interpretation',
        'proposed_test': 'Audit source time origin, censoring and complete-case selection; seek discriminating source data before further inference.',
        'population': 'Referenced bounded lung case slice; no population extrapolation', 'design': 'Prerequisite and data-validity assessment',
        'capability_ids': ['science.acquisition-summary'], 'context_refs': [context]}
    messages_seen = []
    async def respond(messages, info):
        if not any(isinstance(message, ModelResponse) for message in messages):
            code = ('memory=await read_research_memory(query="lung endpoint selection", mission_id="lung-challenge-assessment")\n'
                'assert memory["digests"]\n'
                'f=await prepare_global_frontier(objective="lung endpoint selection", proposals=[' + repr(proposal) + '], limit=5)\n'
                'c=f["candidates"][0]\n'
                'b=await allocate_block(objective=c["objective"], why_now="retained inconclusive method challenge requires prerequisite assessment", '
                'frontier_id=f["frontier_id"], candidate_id=c["candidate_id"])\nb')
            return ModelResponse(parts=[ToolCallPart('run_code', {'code': code}, tool_call_id='next-choice')])
        messages_seen.extend(str(part.content) for message in messages for part in message.parts if hasattr(part, 'content'))
        return ModelResponse(parts=[TextPart('Source-grounded next assessment selected; no scientific resolution claimed.')])
    agents = create_agents('test', 'test', enable_coder=False)
    try:
        with agents.director.override(model=FunctionModel(respond)):
            await agents.director.run('Use retained lung challenge outcome to select a discriminating next assessment', deps=DirectorDeps(runtime))
        allocations = [r for r in store.records(kind=RecordKind.LEDGER_EVENT) if r.payload.get('event_type') == 'DirectorBlockAllocated'
            and r.block_id in {block.block_id for block in runtime.manager.blocks()}]
        if not allocations: raise RuntimeError('next choice not allocated; ' + str(messages_seen[-1:]))
        saved = allocations[-1]
        assert any(ref['seq'] == result.seq for ref in saved.payload['payload']['experience_refs'])
        output = {'database': report['database'], 'allocation_seq': saved.seq, 'allocation': saved.payload, 'source_followup_seq': result.seq,
            'context_reopened': True, 'choice_mode': 'scripted actual Director SDK/tools; no autonomous utility claim',
            'scientific_resolution': 'unknown', 'limitations': ['Broader clinical next-test/challenge labels remain independently unreviewed.']}
        (root / 'var/task9-proof/next-choice.json').write_text(json.dumps(output, indent=2) + '\n')
        print(json.dumps({'status': 'allocated', 'source_followup_seq': result.seq, 'allocation_seq': saved.seq, 'semantic_calls': len(store.records(kind=RecordKind.JEV_CALL))}), flush=True)
    finally:
        await runtime.gdc.aclose(); store.close()


if __name__ == '__main__': asyncio.run(main())
