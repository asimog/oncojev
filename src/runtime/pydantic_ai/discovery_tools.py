"""Role-bounded public metadata tools; never source acquisition or execution."""
from typing import Any, Literal
from uuid import uuid4

from pydantic_ai import RunContext

from src.oncolab.discovery import ExternalDiscovery
from src.oncolab.institution import InstitutionalObservation
from src.persistence.records import RecordKind, StoredRecord
from src.provenance import canonical_bytes


def register_discovery_tools(agent):
    async def lookup(ctx, operation, source, **arguments):
        runtime=ctx.deps.runtime
        block_id=getattr(ctx.deps,'block_id',None)
        if runtime.repository is None:raise ValueError('external discovery requires retained provenance')
        if block_id:runtime.claim(block_id,'source',runtime.max_source_calls)
        else:
            key='director:external_lookups'
            if runtime._counts.get(key,0)>=10:raise RuntimeError('Director metadata allowance exhausted')
            runtime._counts[key]=runtime._counts.get(key,0)+1
        runtime.initialize_institution()
        client=runtime.external_discovery or ExternalDiscovery()
        client.meter = lambda count: runtime.service_resources.charge_download(block_id or 'director', count)
        attempt=str(uuid4())
        request={'source':source,'operation':operation,**arguments}
        try:
            result=await getattr(client,operation)(source,**arguments)
        except Exception as error:
            saved=runtime.repository.store.append(StoredRecord(kind=RecordKind.EXTERNAL_LOOKUP,record_id=attempt,
                block_id=block_id,payload={'request':request,'status':'failed','error_type':type(error).__name__}))
            runtime.institution.observe(InstitutionalObservation(observation_id='external:'+attempt,kind='failure',
                source_seq=saved.seq,payload={'source':source,'error_type':type(error).__name__},provenance='external metadata failure; no scientific negative'))
            raise
        saved=runtime.repository.store.append(StoredRecord(kind=RecordKind.EXTERNAL_LOOKUP,record_id=result.lookup_id,
            block_id=block_id,payload=result.model_dump(mode='json')))
        runtime.institution.observe(InstitutionalObservation(observation_id='external:'+result.lookup_id,
            kind='external_inspection',source_seq=saved.seq,payload={'source':source,'ids':[c.external_id for c in result.cards]},
            provenance='retained mutable-source metadata; not installation or scientific qualification'))
        view=result.model_dump(mode='json',exclude={'raw_json'})
        from src.memory.service import reference
        view['context_reference']=reference(saved).model_dump(mode='json')
        while len(canonical_bytes(view))>32768 and view['cards']:
            view['cards'].pop();view['omitted']+=1
        return view

    @agent.tool
    async def search_external_capabilities(ctx:RunContext[Any],source:Literal["bio.tools"],need:str,filters:dict[str,str]={},
                                            continuation:str|None=None,limit:int=10)->dict[str,Any]:
        """After local contract search, discover public method metadata without executing it."""
        return await lookup(ctx,'search',source,need=need,filters=filters,continuation=continuation,limit=limit)

    @agent.tool
    async def describe_external_capability(ctx:RunContext[Any],source:Literal["bio.tools", "github", "bioconda", "bioconductor"],external_id:str)->dict[str,Any]:
        """Expand one external ID, preserving EDAM/links/licence and blocked execution authority."""
        return await lookup(ctx,'describe',source,external_id=external_id)


    @agent.tool
    async def propose_capability_change(ctx:RunContext[Any],capability_id:str,transition:str,descriptor:dict[str,Any],
        routes:list[dict[str,Any]],scope:dict[str,Any],reference_seqs:list[int],rationale:str,requires_code_change:bool=False)->dict[str,Any]:
        """Retain a reference-linked proposal; Python qualification decides registry acceptance."""
        from src.memory.service import reference
        from src.oncolab.governance import CapabilityProposal, propose
        runtime=ctx.deps.runtime
        if runtime.repository is None:raise ValueError('durable proposal references required')
        runtime.initialize_institution()
        if not 1<=len(reference_seqs)<=30:raise ValueError('bounded references required')
        records=[runtime.repository.store.record_at(seq) for seq in reference_seqs]
        if any(record is None for record in records):raise ValueError('unresolved capability proposal reference')
        proposal=CapabilityProposal(capability_id=capability_id,transition=transition,descriptor=descriptor,routes=routes,scope=scope,
            references=tuple(reference(r) for r in records),rationale=rationale,requires_code_change=requires_code_change,
            parent=runtime.institution.pin().oncolab_registry_revision)
        saved=propose(runtime.institution,proposal)
        runtime.retain_export("capability_proposal:" + saved.record_id)
        return {'proposal_id':saved.record_id,'status':'proposed','authority':'none'}
