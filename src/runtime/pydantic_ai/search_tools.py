"""Agent-facing progressive discovery and block-local suitability tools."""
import asyncio
import unicodedata
from time import perf_counter
from typing import Any
from uuid import uuid4
from pydantic_ai import RunContext

from src.oncolab.execution import check_routes
from src.oncolab.models import OncoLabKind
from src.provenance import canonical_bytes, content_hash
from src.researcher.state import StateFragment
from src.runtime.pydantic_ai.semantic import measure_async


def register_search_page(agent):
    @agent.tool
    async def search_oncolab_page(ctx: RunContext[Any], query: str = "", limit: int = 8, continuation: str | None = None,
                                 kinds: list[str] = [], tags: list[str] = []) -> dict[str, Any]:
        """Compact discovery with stable continuation. Expand IDs explicitly before selection."""
        runtime=ctx.deps.runtime
        block_id=getattr(ctx.deps,"block_id",None)
        key=f"{block_id or 'director'}:index_candidates"
        effective=min(limit,runtime.oncolab_search_k,runtime.oncolab_candidate_k-runtime._counts.get(key,0))
        if effective<1:
            return {"cards":[],"exhausted":False,"status":"retrieval_budget_exhausted","retryable":False}
        kinds=tuple(OncoLabKind(k) for k in kinds)
        page=runtime.index_for(block_id).search_page(query,kinds=kinds,tags=tags,limit=effective,continuation=continuation)
        runtime._counts[key]=runtime._counts.get(key,0)+len(page.cards)
        receipt=runtime.index_receipt("researcher" if block_id else "director","search_page",block_id=block_id,
            query=query,kinds=tuple(kinds),tags=tuple(tags),requested_limit=limit,effective_limit=effective,
            returned_ids=tuple(c.capability_id for c in page.cards),snapshot_id=page.snapshot_id,
            retrieval_version=page.retrieval_version,continuation=continuation,
            contract_hashes={c.capability_id:c.contract_sha256 for c in page.cards})
        return {**page.model_dump(mode="json"),"receipt_id":receipt.receipt_id}


def available_inputs(runtime,block_id,acquisition_ids):
    inputs={}
    for identity in acquisition_ids:
        record=runtime.resolve_acquisition(block_id,identity)
        inputs["acquisition"]=True
        # Availability is obtained from stored rows, not a Researcher declaration.
        for row in record.records:
            for field,value in row.items():
                if value is not None:inputs[field]=inputs.get(field,0)+1
    return inputs


def register_local_semantic_tools(agent):
    @agent.tool
    async def record_dossier_statement(ctx: RunContext[Any], statement: str, epistemic_type: str,
                                       evidence_ids: list[str] = []) -> dict[str, Any]:
        """Resolve exact support first; annotate each statement without changing evidence."""
        from src.dossier.models import DossierStatement
        runtime=ctx.deps.runtime;block_id=ctx.deps.block_id
        identity=content_hash({"statement":statement,"type":epistemic_type,"refs":evidence_ids})
        try:owned_state=runtime.research_state.get(block_id)
        except KeyError:owned_state=runtime.research_state.start(block_id,runtime.manager.block(block_id).objective)
        support=[];missing=[]
        for eid in evidence_ids:
            if runtime.repository is not None:
                value=runtime.memory_service().get_evidence(eid,block_id)
            else:
                item=runtime.evidence.get(eid)
                value={"evidence":item.model_dump(mode="json")} if item and eid in owned_state.evidence_ids else None
            if value is None:missing.append(eid)
            else:support.append(value)
        annotation=DossierStatement(statement_id=identity,statement=statement,epistemic_type=epistemic_type,
            evidence_refs=tuple(evidence_ids),unresolved_refs=tuple(missing),semantic_status="unavailable")
        if not missing and support:
            try:
                result=await measure_async(runtime,block_id,"statement",identity,{"statement":statement,"epistemic_type":epistemic_type,"resolved_support":support})
                annotation=annotation.model_copy(update={"semantic_status":"measured","semantic_call_id":result["call_id"]})
            except Exception:
                pass # Terminal summary must remain constructible; failures have receipts.
        try:state=runtime.research_state.get(block_id)
        except KeyError:state=runtime.research_state.start(block_id,runtime.manager.block(block_id).objective)
        runtime.persist_state(state.append("candidates",StateFragment(fragment_id=identity,kind="dossier_statement",summary=statement,
            provenance=tuple(evidence_ids) or ("researcher-statement",),details=annotation.model_dump(mode="json"))))
        return annotation.model_dump(mode="json")

    @agent.tool
    async def assess_method(ctx: RunContext[Any], capability_id: str, need: dict[str, Any], acquisition_ids: list[str] = [],
                            operation: str | None = None) -> dict[str, Any]:
        """Describe an ID, check owned inputs/routes, measure semantic fit; never grants execution."""
        runtime=ctx.deps.runtime; block_id=ctx.deps.block_id
        contract=runtime.index_for(block_id).describe_with_verification(capability_id)
        if contract is None:raise ValueError("unknown capability ID")
        receipt=runtime.index_receipt("researcher","describe",block_id=block_id,requested_id=capability_id,
            returned_ids=(capability_id,),contract_hashes={capability_id:contract["contract_sha256"]},snapshot_id=runtime.index_for(block_id).snapshot_id)
        checks=check_routes(runtime.index_for(block_id).describe(capability_id),available_inputs(runtime,block_id,acquisition_ids),operation,routes=runtime.index_for(block_id).routes)
        payload={"need":need,"contract":contract["descriptor"],"execution_routes":contract["execution_routes"],"checks":checks,
                 "contract_sha256":contract["contract_sha256"],"description_receipt":receipt.receipt_id,"snapshot_id":runtime.index_for(block_id).snapshot_id}
        result=await measure_async(runtime,block_id,"method",capability_id,payload,eligible=checks["eligible"])
        assessment={**result,"checks":checks,"contract_sha256":contract["contract_sha256"],"need_sha256":content_hash(need)}
        runtime.method_assessments[f"{block_id}:{capability_id}"]=assessment
        return assessment

    @agent.tool
    async def assess_representation(ctx: RunContext[Any], acquisition_id: str, need: dict[str, Any]) -> dict[str, Any]:
        """Measure sufficiency over an actually owned acquisition's bounded summary."""
        runtime=ctx.deps.runtime; record=runtime.resolve_acquisition(ctx.deps.block_id,acquisition_id)
        fields=sorted({k for row in record.records for k in row})
        representation={"acquisition_id":acquisition_id,"source":record.source,"content_sha256":record.content_sha256,
            "fields":fields[:40],"omitted_fields":max(0,len(fields)-40),"rows":len(record.records),
            "limitations":["Stored response slice; population completeness unknown."],
            "available_counts":{k:sum(row.get(k) is not None for row in record.records) for k in fields[:40]}}
        return await measure_async(runtime,ctx.deps.block_id,"representation",acquisition_id,{"need":need,"representation":representation},eligible=bool(record.records),escalate=True)

    @agent.tool
    async def assess_hypothesis(ctx: RunContext[Any], hypothesis: str, proposed_test: str) -> dict[str, Any]:
        """Exact normalized duplicates before bounded semantic alignment/similarity."""
        runtime=ctx.deps.runtime; block_id=ctx.deps.block_id
        def normalized(text):return " ".join(unicodedata.normalize("NFKC",text).casefold().split())
        identity=content_hash({"statement":normalized(hypothesis),"test":normalized(proposed_test)})
        try:state=runtime.research_state.get(block_id)
        except KeyError:state=runtime.research_state.start(block_id,runtime.manager.block(block_id).objective)
        memory=runtime.memory_service()
        historical=list(memory.items("hypotheses",hypothesis,limit=5)) if memory else []
        prior=[f.details for f in state.candidates if f.kind=="hypothesis"]
        prior.extend({"statement":i["summary"],"proposed_test":i.get("details",{}).get("proposed_test")} for i in historical)
        duplicate=next((i for i in prior if normalized(i.get("statement",""))==normalized(hypothesis)
                        and normalized(i.get("proposed_test") or "")==normalized(proposed_test)),None)
        if duplicate:
            runtime.append_event(block_id,"HypothesisExactDuplicate",{"identity":identity,"hypothesis":hypothesis,"proposed_test":proposed_test})
            return {"identity":identity,"exact_duplicate":True,"semantic_called":False,"epistemic_status":"hypothesis"}
        payload={"objective":state.objective,"hypothesis":hypothesis,"proposed_test":proposed_test,"prior_hypotheses":prior[:10]}
        result=await measure_async(runtime,block_id,"hypothesis",identity,payload,escalate=True)
        runtime.persist_state(state.append("candidates",StateFragment(fragment_id=identity,kind="hypothesis",summary=hypothesis,
            provenance=(result["call_id"],),details={"statement":hypothesis,"proposed_test":proposed_test})))
        return {**result,"identity":identity,"exact_duplicate":False}

    return {"assess_hypothesis":assess_hypothesis}


async def semantic_memory_context_async(runtime,query,*,limit=5,block_id=None,**filters):
    from src.memory.models import MemoryRetrievalReceipt
    from src.persistence.records import RecordKind
    started=perf_counter()
    memory=runtime.memory_service()
    if memory is None:return {"digests":[],"semantic_status":"no_memory"}
    context=memory.context(query,limit=limit,**filters).model_dump(mode="json")
    context["semantic_status"]="deterministic_fallback"
    def finish():
        context["retrieval_receipt_id"]=str(uuid4())
        # Native distributions are durably available by call ID; agent context
        # need not repeat an arbitrarily large annotation set.
        if len(canonical_bytes(context))>32768:
            context["measurements"]=[{"call_id":m["call_id"],"projection_id":m["projection_id"]} for m in context.get("measurements",[])]
        while len(canonical_bytes(context))>32768 and context["digests"]:
            context["digests"].pop();context["omitted_digests"]+=1
        receipt=MemoryRetrievalReceipt(receipt_id=context["retrieval_receipt_id"],query=query[:1000],mission_id=runtime.mission_id,cycle_id=runtime.cycle_id,block_id=block_id,
            digest_ids=tuple(d["digest_id"] for d in context["digests"]),status=context["semantic_status"],failure_type=context.get("semantic_failure"),
            semantic_call_ids=tuple(m["call_id"] for m in context.get("measurements",[])),
            resources={"calls":runtime._counts.get("memory_jev",0),"questions":runtime._counts.get("memory_questions",0),
                       "bytes":runtime._counts.get("memory_bytes",0),"elapsed_seconds":runtime.memory_elapsed},duration_ms=(perf_counter()-started)*1000)
        if runtime.repository is not None:runtime.repository.record_immutable(RecordKind.MEMORY_RETRIEVAL,receipt.receipt_id,receipt,block_id)
        context["retrieval_receipt_id"]=receipt.receipt_id
        return context
    if not runtime.enable_jev or not context["digests"]:return finish()
    measurements=[]; scores={}
    comparison=[{"digest_id":d["digest_id"],"objectives":d["objectives"],"hypotheses":d["hypotheses"],"uncertainties":d["uncertainties"]} for d in context["digests"][:5]]
    try:
        for digest in context["digests"][:min(5,runtime.memory_limit)]:
            payload={"objective":query,"memory":{k:digest[k] for k in ("digest_id","objectives","cycle_status","failure_reason","hypotheses","operational_blockers","uncertainties","limitations","candidates")},
                     "comparison":[d for d in comparison if d["digest_id"]!=digest["digest_id"]]}
            result=await measure_async(runtime,block_id,"memory",digest["digest_id"],payload)
            measurements.append(result)
            scores[digest["digest_id"]]=next((d["p_true"] for d in result["decisions"] if d["question_id"].endswith(":relevance")),0)
    except Exception as error:
        context["semantic_failure"]=type(error).__name__
        context["measurements"]=measurements
        return finish() # Exact deterministic ordering, explicit operational fallback.
    context["digests"].sort(key=lambda d:(-scores.get(d["digest_id"],0),d["digest_id"]))
    context["semantic_status"]="measured_context"
    context["measurements"]=measurements
    # Never let annotations turn the F3 envelope into an unbounded context.
    return finish()


def semantic_memory_context(*args, **kwargs):
    """Synchronous offline inspection boundary."""
    return asyncio.run(semantic_memory_context_async(*args, **kwargs))
