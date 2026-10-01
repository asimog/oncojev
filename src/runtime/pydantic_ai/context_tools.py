"""Researcher-only context assessment over exact retained scientific/source records."""
from uuid import uuid4
from typing import Any
from pydantic_ai import RunContext
from src.memory.literature import LiteratureContext, LiteratureContextPolicy, category_from_native
from src.memory.service import reference
from src.persistence.records import RecordKind
from src.persistence.references import resolve_reference
from src.provenance import content_hash
from src.science.models import ScientificAttempt
from src.sources.models import LiteratureSearchResult
from src.runtime.pydantic_ai.semantic import measure_async


def register_context_tools(agent):
    @agent.tool
    async def assess_literature_context(ctx: RunContext[Any], analysis_id: str, claim: str,
                                        literature_ids: list[str]) -> dict[str, Any]:
        """Annotate a retained source analysis using selected searches; never changes evidence.

        Include relevant/contrary reports. Empty/title-only searches leave classification
        unknown. Scope must be established by supplied material, never pretrained knowledge.
        """
        runtime = ctx.deps.runtime; block_id = ctx.deps.block_id
        runtime.claim(block_id, "tool", runtime.max_tool_calls)
        if runtime.repository is None:
            raise ValueError("literature context requires retained scientific/source lineage")
        if not claim.strip() or len(claim) > 1000 or not 1 <= len(literature_ids) <= 3 or len(set(literature_ids)) != len(literature_ids):
            raise ValueError("bounded claim and one to three distinct retained searches required")
        store = runtime.repository.store
        records = store.records(block_id=block_id)
        attempt_record = next((r for r in reversed(records) if r.kind == RecordKind.SCIENTIFIC_ATTEMPT
            and r.payload.get("stage") == "completed" and r.payload.get("analysis", {}).get("analysis_id") == analysis_id), None)
        if attempt_record is None:
            raise ValueError("context requires an owned completed source analysis")
        attempt = ScientificAttempt.model_validate(attempt_record.payload)
        measurement = resolve_reference(store, attempt.measurement_reference)
        source = resolve_reference(store, attempt.input_reference)
        if (measurement.get("origin") != "source" or measurement.get("source_refs") != [attempt.input_reference.value]
            or measurement.get("input_sha256") != source.get("content_sha256")):
            raise ValueError("context requires exact source-bound measurement identity")
        basis = [reference(attempt_record)]
        for ref in (attempt.measurement_reference, attempt.input_reference):
            basis.append(reference(next(r for r in reversed(records) if r.kind.value == ref.kind
                and r.record_id == ref.value and content_hash(r.payload) == ref.sha256)))
        if attempt.hypothesis_record_seq:
            hypothesis = store.record_at(attempt.hypothesis_record_seq)
            if hypothesis is None or hypothesis.kind != RecordKind.STATE_REVISION or not any(
                f.get("kind") == "hypothesis" and f.get("fragment_id") == attempt.analysis.test_plan.hypothesis_id
                for f in hypothesis.payload.get("candidates", ())):
                raise ValueError("unresolved scientific hypothesis lineage")
            basis.append(reference(hypothesis))
        for r in records:
            if r.kind == RecordKind.EVIDENCE and r.payload.get("measurement") == measurement:
                basis.append(reference(r))
        searches = []
        for identity in literature_ids:
            record = next((r for r in records if r.kind == RecordKind.LITERATURE and r.record_id == identity), None)
            if record is None:
                raise ValueError("literature search is not owned by this block")
            search = LiteratureSearchResult.model_validate(record.payload)
            if search.content_sha256 != record.payload.get("content_sha256"):
                raise ValueError("literature content identity mismatch")
            basis.append(reference(record)); searches.append(search)
        failures = [r for r in records if r.kind == RecordKind.LEDGER_EVENT
            and r.payload.get("event_type") == "CapabilityFailure"
            and r.payload.get("payload", {}).get("capability_id") == "literature.public"]
        failed_invocations = {r.payload["payload"].get("invocation_id") for r in failures}
        basis.extend(reference(r) for r in records if r in failures or r.kind == RecordKind.LEDGER_EVENT
            and r.payload.get("event_type") == "CapabilityInvocation"
            and r.payload.get("payload", {}).get("invocation_id") in failed_invocations)
        # Keep the full attempt history reference-resolvable; no prose can declare replication.
        related = [r for r in store.records(kind=RecordKind.SCIENTIFIC_ATTEMPT)
            if r.payload.get("stage") != "started" and (
                (r.payload.get("analysis", {}).get("test_plan") or {}).get("hypothesis_id") == attempt.analysis.test_plan.hypothesis_id
                if attempt.analysis.test_plan else r.block_id == block_id and r.payload.get("analysis", {}).get("analysis_id") == analysis_id)]
        history = [{"reference": reference(r).model_dump(mode="json"), "stage": r.payload.get("stage"),
                    "outcome": r.payload.get("outcome"), "analysis": r.payload.get("analysis"),
                    "input_reference": r.payload.get("input_reference"), "measurement_reference": r.payload.get("measurement_reference"),
                    "limitations": r.payload.get("limitations")} for r in related[:10]]
        basis.extend(reference(r) for r in related[:10] if r.seq != attempt_record.seq)
        challenges=[]
        for record in store.records(kind=RecordKind.FOLLOWUP_RESULT):
            current=attempt.measurement_reference.model_dump(mode="json")
            if current not in (record.payload.get("baseline_measurement"),record.payload.get("target_measurement")): continue
            plan=next((r for r in store.records(kind=RecordKind.FOLLOWUP_PLAN,block_id=record.block_id) if r.record_id==record.record_id),None)
            if plan is not None:
                challenges.append({"declaration":plan.payload,"result":record.payload,
                    "references":[reference(plan).model_dump(mode="json"),reference(record).model_dump(mode="json")]})
                if len(challenges)<=5: basis.extend((reference(plan),reference(record)))
        assessment = LiteratureContext(assessment_id=str(uuid4()), block_id=block_id, claim=claim,
            basis=tuple(basis), semantic_status="insufficient_material")
        material = any(record.abstract and not record.abstract_truncated for search in searches for record in search.records)
        unresolved = []
        if not material:
            unresolved.append("No complete retained abstract; titles, missing reports and empty searches cannot classify this finding.")
        if failures:
            unresolved.append("Owned literature searches have operational failures; coverage remains unresolved.")
        if len(related) > 10:
            unresolved.append(f"{len(related)-10} related attempt records omitted from semantic projection.")
        if len(failures) > 5:
            unresolved.append(f"{len(failures)-5} failed searches omitted from semantic projection; exact failure references remain retained.")
        if len(challenges)>5: unresolved.append(f"{len(challenges)-5} scientific follow-up comparisons omitted from semantic projection.")
        if material:
            payload = {"claim": claim, "analysis_contract": attempt.analysis.model_dump(mode="json", exclude={"inputs"}),
                "measurement": measurement, "source_scope": {"source": source.get("source"), "request": source.get("request"),
                "coverage": source.get("coverage")}, "literature": [s.model_dump(mode="json") for s in searches],
                "history": history, "challenge_history":challenges[:5], "search_failures": [r.payload for r in failures[:5]], "unresolved": unresolved, "limitations": assessment.limitations}
            try:
                result = await measure_async(runtime, block_id, "literature_context", assessment.assessment_id,
                    payload, policy=LiteratureContextPolicy())
                category, reason = category_from_native(result["decisions"])
                if category == "potentially_novel_observation" and (measurement.get("interpretation") != "associative" or failures or any(s.coverage is None
                    or s.coverage.reported_total is None or s.coverage.reported_total > len(s.records)
                    or not s.records or any(not r.abstract or r.abstract_truncated for r in s.records) for s in searches)):
                    category, reason = "unknown", "Incomplete/failed retained query coverage cannot support a potential-novelty annotation."
                if reason: unresolved.append(reason)
                assessment = assessment.model_copy(update={"category": category, "semantic_status": "measured", "semantic_call_id": result["call_id"]})
                call = next(r for r in reversed(store.records(kind=RecordKind.JEV_CALL, block_id=block_id))
                            if r.record_id == result["call_id"] and r.payload.get("outcome") == "completed")
                basis.append(reference(call))
            except Exception as error:
                unresolved.append(f"Context measurement unavailable: {type(error).__name__}; no classification inferred.")
                assessment = assessment.model_copy(update={"category": "unknown", "semantic_status": "unavailable"})
                # Failed/partial native receipts remain in the standard Jev ledger.
                call = next((r for r in reversed(store.records(kind=RecordKind.JEV_CALL, block_id=block_id))
                    if r.payload.get("context_identity") == assessment.assessment_id), None)
                if call is not None: basis.append(reference(call))
        assessment = LiteratureContext.model_validate(assessment.model_copy(update={"unresolved": tuple(unresolved), "basis": tuple(basis)}).model_dump())
        runtime.repository.record_immutable(RecordKind.LITERATURE_CONTEXT, assessment.assessment_id, assessment, block_id)
        runtime.append_event(block_id, "LiteratureContextAssessed", {"assessment_id": assessment.assessment_id,
            "category": assessment.category, "epistemic_status": assessment.epistemic_status})
        return assessment.model_dump(mode="json")
