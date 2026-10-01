"""Source-resolved scientific operations; no caller-supplied origin labels."""
from typing import Any
from pydantic_ai import RunContext
from src.persistence.records import RecordKind
from src.researcher.state import StateFragment
from src.science.models import AnalysisSpec, HypothesisTestPlan, ScientificAttempt, InvalidAnalysis
from src.provenance import ExecutionReference, content_hash


def register_scientific_tools(agent):
    @agent.tool
    async def combine_acquisition_pages(ctx:RunContext[Any],acquisition_ids:list[str])->dict[str,Any]:
        """Combine contiguous ordered source pages; rejects overlap, changing totals and mixed queries."""
        from src.sources.coverage import combine_pages
        runtime=ctx.deps.runtime;block_id=ctx.deps.block_id
        runtime.claim(block_id,"tool",runtime.max_tool_calls)
        if not 1<=len(acquisition_ids)<=20:raise ValueError("bounded page list required")
        record=combine_pages(tuple(runtime.resolve_acquisition(block_id,i) for i in acquisition_ids))
        runtime.retain_acquisition(block_id,record)
        runtime.append_event(block_id,"AcquisitionPagesCombined",{"acquisition_id":record.acquisition_id,"pages":acquisition_ids,"coverage":record.coverage.model_dump(mode="json")})
        return record.model_dump(mode="json")

    @agent.tool
    async def acquire_gdc_file(ctx:RunContext[Any],file_id:str,format:str)->dict[str,Any]:
        """Retain exact bytes from a bounded explicitly open GDC file; returns metadata, not bytes."""
        runtime=ctx.deps.runtime;block_id=ctx.deps.block_id
        if runtime.repository is None:raise ValueError("file acquisition requires durable storage")
        runtime.claim(block_id,"source",runtime.max_source_calls)
        from uuid import uuid4
        call_id=str(uuid4())
        runtime.index_receipt("researcher","execute",block_id=block_id,selected_id="source.gdc-file")
        runtime.append_event(block_id,"CapabilityInvocation",{"invocation_id":call_id,"capability_id":"source.gdc-file","file_id":file_id})
        try:
            artifact=await runtime.gdc.acquire_file(file_id,block_id,format)
            runtime.repository.record_scientific_artifact(artifact)
        except Exception as error:
            runtime.append_event(block_id,"CapabilityFailure",{"invocation_id":call_id,"capability_id":"source.gdc-file","error_type":type(error).__name__})
            raise
        runtime.append_event(block_id,"CapabilityResult",{"invocation_id":call_id,"capability_id":"source.gdc-file","artifact_id":artifact.artifact_id,"response_bytes":artifact.size_bytes})
        return artifact.model_dump(mode="json",exclude={"content_base64"}) | {"sandbox_path":f"/input/artifacts/{artifact.byte_sha256}"}

    @agent.tool
    async def run_source_analysis(ctx:RunContext[Any],acquisition_id:str,analysis_id:str,question:str,population:str,
                                  estimand:str,method:str,fields:dict[str,str],entity_field:str,entity_unit:str,
                                  design:str,transformations:dict[str,str]={},replication_id:str|None=None,
                                  test_plan:dict[str,Any]|None=None)->dict[str,Any]:
        """Complete-row Pearson or OLS over owned retained inputs with explicit entity/design contract."""
        runtime=ctx.deps.runtime;block_id=ctx.deps.block_id
        runtime.claim(block_id,"tool",runtime.max_tool_calls)
        record=runtime.resolve_acquisition(block_id,acquisition_id)
        spec=AnalysisSpec(analysis_id=analysis_id,question=question,population=population,estimand=estimand,method=method,
            variables=tuple(fields),fields=fields,entity_field=entity_field,entity_unit=entity_unit,design=design,
            transformations=transformations,source_refs=(acquisition_id,),replication_id=replication_id,
            test_plan=HypothesisTestPlan.model_validate(test_plan) if test_plan is not None else None)
        from uuid import uuid4
        call_id=str(uuid4());capability="science.source-paired"
        runtime.index_receipt("researcher","execute",block_id=block_id,selected_id=capability)
        hypothesis_seq = None
        if spec.test_plan:
            if runtime.repository is None:
                raise ValueError("hypothesis testing requires persisted hypothesis lineage")
            states = runtime.repository.store.records(kind=RecordKind.STATE_REVISION)
            origin = next((r for r in reversed(states) if any(f.get("kind") == "hypothesis" and
                f.get("fragment_id") == spec.test_plan.hypothesis_id for f in r.payload.get("candidates", ()))), None)
            if origin is None:
                raise ValueError("test plan must reference a retained hypothesis, never an invented identity")
            hypothesis_seq = origin.seq
        attempt = ScientificAttempt(attempt_id=call_id, block_id=block_id, capability_id=capability, analysis=spec,
            input_reference=ExecutionReference(kind="acquisition", value=acquisition_id,
                sha256=content_hash(record.model_dump(mode="json")), block_id=block_id),
            hypothesis_record_seq=hypothesis_seq, stage="started", outcome="attempted")
        def retain(value):
            if runtime.repository:
                runtime.repository.record_immutable(RecordKind.SCIENTIFIC_ATTEMPT,
                    value.attempt_id + ":" + value.stage, value, block_id)
        retain(attempt)
        runtime.append_event(block_id,"CapabilityInvocation",{"invocation_id":call_id,"capability_id":capability,"analysis_id":analysis_id,"method":method})
        try:result=await runtime.heavy_operation(block_id,runtime.science.execute_source,record.model_copy(deep=True),spec.model_copy(deep=True))
        except BaseException as error:
            import asyncio
            invalid = isinstance(error, InvalidAnalysis)
            stage = "invalid" if invalid else "interrupted" if isinstance(error, asyncio.CancelledError) else "operational_failed"
            retain(attempt.model_copy(update={"stage":stage, "outcome":"invalid" if invalid else "attempted", "failure_type":type(error).__name__}))
            runtime.append_event(block_id,"CapabilityFailure",{"invocation_id":call_id,"capability_id":capability,"error_type":type(error).__name__, "scientific_invalid":invalid})
            raise
        runtime.measurements[(block_id,analysis_id)]=result
        try:state=runtime.research_state.get(block_id)
        except KeyError:state=runtime.research_state.start(block_id,runtime.manager.block(block_id).objective)
        runtime.persist_state(state.add_measurement(result))
        if runtime.repository is not None:
            with runtime.repository.store.transaction():
                runtime.repository.record_measurement(result,block_id)
                retain(attempt.model_copy(update={"stage":"completed",
                    "outcome":result.diagnostics.get("hypothesis_test", {}).get("outcome", "unknown"),
                    "measurement_reference":ExecutionReference(kind="measurement", value=analysis_id,
                        sha256=content_hash(result.model_dump(mode="json")), block_id=block_id)}))
        runtime.append_event(block_id,"ScienceMeasurement",{"analysis_id":analysis_id,"method":method,"analysis_key":result.analysis_key})
        runtime.append_event(block_id,"CapabilityResult",{"invocation_id":call_id,"capability_id":capability,"analysis_id":analysis_id,"origin":"source"})
        runtime.verification(block_id,capability,analysis_id,"measurement",result,"Paired complete-row association over stored source slice; assumptions and population representativeness not established.")
        return result.model_dump(mode="json")
