"""Researcher declarations and exact lineage for deterministic follow-up comparisons."""
from typing import Any
from uuid import UUID, uuid4
from pydantic_ai import RunContext
from src.persistence.records import RecordKind
from src.persistence.references import resolve_reference
from src.provenance import ExecutionReference, content_hash
from src.science.models import AnalysisSpec, ScientificAttempt, MeasuredResult
from src.science.followup import FollowupPlan, FollowupResult, compare_followup, canonical_case_ids
from src.sources.models import AcquisitionRecord


def register_followup_tools(agent):
    @agent.tool
    async def declare_source_followup(ctx: RunContext[Any], baseline_analysis_id: str, comparison_id: str,
        kind: str, target_analysis: dict[str, Any], target_request: dict[str, Any],
        expected_discrimination: str, alternative_explanations: list[str], baseline_block_id: str | None = None) -> dict[str, Any]:
        """Freeze a paired-association challenge before accessing new confirmation results.

        Independent replication requires fresh GDC case queries and fixed preprocessing.
        Include comparison_id in the target's explicit multiplicity family. Same-participant
        changes are sensitivity checks, not independent replication. Declare exact request.
        """
        runtime=ctx.deps.runtime; block_id=ctx.deps.block_id
        runtime.claim(block_id,"tool",runtime.max_tool_calls)
        if runtime.repository is None: raise ValueError("follow-up requires durable scientific lineage")
        store=runtime.repository.store
        baseline_block_id=baseline_block_id or block_id
        stored=next((r for r in reversed(store.records(kind=RecordKind.SCIENTIFIC_ATTEMPT,block_id=baseline_block_id))
            if r.payload.get("stage")=="completed" and r.payload.get("analysis",{}).get("analysis_id")==baseline_analysis_id),None)
        if stored is None: raise ValueError("missing completed source baseline")
        baseline=ScientificAttempt.model_validate(stored.payload)
        measurement=resolve_reference(store,baseline.measurement_reference)
        source=AcquisitionRecord.model_validate(resolve_reference(store,baseline.input_reference))
        if measurement.get("origin")!="source" or source.source!="gdc" or source.coverage is None or source.coverage.endpoint!="cases":
            raise ValueError("follow-up requires a retained GDC case-paired baseline")
        plan=FollowupPlan(followup_id=str(uuid4()),block_id=block_id,comparison_id=comparison_id,kind=kind,
            baseline_attempt_id=stored.record_id,baseline_measurement=baseline.measurement_reference,
            baseline_input=baseline.input_reference,baseline_analysis=baseline.analysis,
            target_analysis=AnalysisSpec.model_validate(target_analysis),target_request=target_request,
            expected_discrimination=expected_discrimination,alternative_explanations=tuple(alternative_explanations))
        for prior in store.records(kind=RecordKind.FOLLOWUP_PLAN):
            previous=FollowupPlan.model_validate(prior.payload)
            if previous.target_analysis.test_plan.hypothesis_id==plan.target_analysis.test_plan.hypothesis_id and previous.target_analysis.test_plan!=plan.target_analysis.test_plan:
                raise ValueError("the retained hypothesis follow-up family, alpha, direction and effect threshold are already frozen")
        if kind=="independent_replication" and any(r.payload.get("source")=="gdc" and
            r.payload.get("request")==target_request for r in store.records(kind=RecordKind.ACQUISITION)):
            raise ValueError("confirmation query has already been accessed; declare a fresh query or sensitivity check")
        runtime.repository.record_immutable(RecordKind.FOLLOWUP_PLAN,plan.followup_id,plan,block_id)
        return plan.model_dump(mode="json")


def prepare_followup(runtime,block_id,identity,source,spec):
    if runtime.repository is None: raise ValueError("follow-up requires durable storage")
    store=runtime.repository.store
    stored=next((r for r in store.records(kind=RecordKind.FOLLOWUP_PLAN,block_id=block_id) if r.record_id==identity),None)
    if stored is None: raise ValueError("follow-up declaration is not owned by this block")
    plan=FollowupPlan.model_validate(stored.payload)
    if any(r.record_id==identity for r in store.records(kind=RecordKind.FOLLOWUP_RESULT,block_id=block_id)):
        raise ValueError("follow-up already has a terminal result; declare a new comparison")
    if source.source!="gdc" or source.origin!="public" or source.coverage is None or source.coverage.endpoint!="cases" or source.request!=plan.target_request:
        raise ValueError("target acquisition does not match frozen follow-up source query")
    if spec.model_dump(mode="json",exclude={"source_refs"})!=plan.target_analysis.model_dump(mode="json",exclude={"source_refs"}):
        raise ValueError("analysis changed after follow-up declaration")
    acquisition=next(r for r in store.records(kind=RecordKind.ACQUISITION,block_id=block_id) if r.record_id==source.acquisition_id)
    if plan.kind=="independent_replication" and (acquisition.seq<=stored.seq or source.retrieved_at<stored.recorded_at):
        raise ValueError("confirmation input was accessed before the follow-up declaration")
    baseline=MeasuredResult.model_validate(resolve_reference(store,plan.baseline_measurement))
    baseline_input=AcquisitionRecord.model_validate(resolve_reference(store,plan.baseline_input))
    access="not_applicable" if plan.kind!="independent_replication" else "fresh_local_query"
    identities=canonical_case_ids(source)
    if plan.kind=="independent_replication":
        if identities is None: access="unknown"
        else:
            for prior in store.records(kind=RecordKind.ACQUISITION):
                if prior.seq>=stored.seq or prior.payload.get("source")!="gdc" or (prior.payload.get("coverage") or {}).get("endpoint")!="cases": continue
                for row in prior.payload.get("records",()):
                    values=[]
                    for field in spec.fields.values():
                        value=row
                        for part in field.split("."):
                            value=value.get(part) if isinstance(value,dict) else None
                        values.append(value)
                    if not all(value is not None for value in values): continue
                    try: canonical=str(UUID(str(row.get("case_id") or row.get("id"))))
                    except ValueError:
                        if access!="previously_accessed": access="unknown"
                        continue
                    if canonical in identities: access="previously_accessed"
    return plan,baseline,baseline_input,access


def retain_followup(runtime,prepared,source,*,measurement=None,stage="completed",failure_type=None):
    plan,baseline,baseline_input,access=prepared
    if measurement is not None:
        target=ExecutionReference(kind="measurement",value=measurement.analysis_id,block_id=plan.block_id,
                                  sha256=content_hash(measurement.model_dump(mode="json")))
        result=compare_followup(plan,baseline,measurement,baseline_input,source,target,confirmation_access=access)
    else:
        result=FollowupResult(followup_id=plan.followup_id,block_id=plan.block_id,
            baseline_measurement=plan.baseline_measurement,target_input=ExecutionReference(kind="acquisition",
                value=source.acquisition_id,block_id=plan.block_id,sha256=content_hash(source.model_dump(mode="json"))),
            stage=stage,outcome="invalid" if stage=="invalid" else "attempted",confirmation_access=access,
            unresolved=(f"Target analysis did not establish a comparison: {failure_type}.",),limitations=plan.limitations)
    result=FollowupResult.model_validate(result.model_dump(mode="json"))
    runtime.repository.record_immutable(RecordKind.FOLLOWUP_RESULT,plan.followup_id,result,plan.block_id)
    return result
