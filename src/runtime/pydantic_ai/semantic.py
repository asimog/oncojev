"""Composition of bounded semantic measurement within the existing runtime.

This is receipt/budget plumbing, not an agent or an admission authority.
"""
import asyncio
from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from src.jev.failure import JevOperationalFailure
from src.jev.frontier import FrontierPolicy
from src.jev.models import JevCallReceipt, JevExecutionFailure, JevFailureCategory
from src.jev.questions import semantic_questions
from src.provenance import canonical_bytes, content_hash
from src.researcher.state import JevProjection, ProjectionSpec


async def measure_async(runtime, block_id, context_type, identity, payload, *, eligible=True, escalate=False):
    """One versioned context, independent questions, native receipt and policy.

    Director Control uses a separate global retrieval allocation; it has no
    scientific tools. Failed batches preserve valid partial answers for inspection
    but never feed the frontier. The caller explicitly chooses its fallback.
    """
    if not runtime.enable_jev:
        raise RuntimeError("Jev disabled in this evaluation condition")
    spec=ProjectionSpec(projection_name=context_type,candidate_id=identity,
                        max_items=runtime.projection_max_items,max_payload_bytes=runtime.projection_max_payload_bytes)
    digest=content_hash({"spec":spec.model_dump(mode="json"),"payload":payload})
    projection=JevProjection(projection_id=f"{context_type}-v1-{digest[:16]}",payload=payload,
                            payload_sha256=content_hash(payload),spec=spec,provenance=(context_type,"semantic-context-v1"))
    questions=semantic_questions(context_type,identity,projection.projection_id)
    if block_id is not None:
        runtime.check_work(block_id,{"jev":(1,runtime.max_jev_calls),"jev_questions":(len(questions),runtime.max_jev_questions)})
        runtime.claim(block_id,"jev",runtime.max_jev_calls)
        key=f"{block_id}:jev_questions"
        runtime._counts[key]=runtime._counts.get(key,0)+len(questions)
        runtime.append_event(block_id,"ResourceAttempt",{"resource":"jev_questions","attempt":runtime._counts[key],"limit":runtime.max_jev_questions})
    else:
        runtime.claim_memory_measurement(len(questions),len(canonical_bytes({"state":payload,"questions":[q.model_dump(mode="json") for q in questions]})))
    receipt=JevCallReceipt(call_id=str(uuid4()),block_id=block_id,mission_id=runtime.mission_id,cycle_id=runtime.cycle_id,
        context_type=context_type,context_identity=identity,candidate_id=identity,candidate_summary=str(payload.get("objective",payload.get("need","")))[:2000],
        started_at=datetime.now(UTC),duration_ms=0,outcome="started",model_requested=getattr(runtime.jev,"model_requested","unreported"),
        projection=projection.model_dump(mode="json"),projection_sha256=projection.payload_sha256,questions=questions,
        question_hashes=tuple(content_hash(q.model_dump(mode="json")) for q in questions),policy_version=FrontierPolicy.version)
    def record(value):
        if runtime.repository is not None:runtime.repository.record_jev_call(value)
    record(receipt)
    started=perf_counter()
    try:
        if len(canonical_bytes(payload))>spec.max_payload_bytes:
            raise ValueError("semantic context exceeds byte bound; expand fewer contracts")
        decisions=await runtime.evaluate_jev(payload,questions)
        if len(decisions)!=len(questions) or {d.question_id for d in decisions}!={q.question_id for q in questions}:
            raise ValueError("incomplete semantic batch")
    except Exception as error:
        if block_id is None:runtime.memory_elapsed+=perf_counter()-started
        failures=error.failures if isinstance(error,JevOperationalFailure) else (JevExecutionFailure(question_id="__batch__",category=JevFailureCategory.VALIDATION,detail=type(error).__name__),)
        record(receipt.model_copy(update={"outcome":"failed","duration_ms":(perf_counter()-started)*1000,
            "failures":failures,"decisions":tuple(getattr(error,"decisions",())),"reported_metadata":getattr(error,"metadata",None),
            "models_resolved":tuple(sorted({d.model_resolved for d in getattr(error,"decisions",())}))}))
        if block_id is not None:
            runtime.append_event(block_id,"JevExecutionFailure",{"call_id":receipt.call_id,"context_type":context_type,"categories":[f.category.value for f in failures]})
            if runtime.repository is not None:runtime.repository.record_jev_failure(block_id,failures)
        raise
    if block_id is None:runtime.memory_elapsed+=perf_counter()-started
    receipt=receipt.model_copy(update={"outcome":"completed","duration_ms":(perf_counter()-started)*1000,"decisions":tuple(decisions),
        "models_resolved":tuple(sorted({d.model_resolved for d in decisions})),"reported_metadata":getattr(decisions,"metadata",None)})
    record(receipt)
    frontier=FrontierPolicy().interpret(identity,decisions,questions,(receipt.call_id,projection.projection_id),eligible=eligible,escalate=escalate)
    result={"call_id":receipt.call_id,"context_type":context_type,"projection_id":projection.projection_id,"projection_sha256":projection.payload_sha256,
            "policy_version":receipt.policy_version,"decisions":[d.model_dump(mode="json") for d in decisions],
            "frontier":frontier.model_dump(mode="json"),"eligible":eligible,"epistemic_status":"semantic_search_history"}
    if block_id is not None:
        runtime.jev_history.setdefault(block_id,[]).extend(decisions)
        runtime.append_event(block_id,"JevExecution",{"call_id":receipt.call_id,"question_ids":[q.question_id for q in questions],"projection_id":projection.projection_id})
        runtime.append_event(block_id,"FrontierDecision",{**result,**frontier.model_dump(mode="json"),"candidate_summary":receipt.candidate_summary})
        if runtime.repository is not None:runtime.repository.record_jev_decisions(block_id,decisions)
    return result


def measure(*args, **kwargs):
    """Offline evaluation boundary; the composition remains the async owner path."""
    return asyncio.run(measure_async(*args, **kwargs))
