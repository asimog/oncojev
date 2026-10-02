"""Source-resolved scientific operations; no caller-supplied origin labels."""
from typing import Any
from pydantic_ai import RunContext
from src.persistence.records import RecordKind
from src.researcher.state import StateFragment
from src.science.models import AnalysisSpec, HypothesisTestPlan, ScientificAttempt, InvalidAnalysis
from src.provenance import ExecutionReference, content_hash


def register_scientific_tools(agent):
    @agent.tool
    async def run_reusable_method(ctx: RunContext[Any], capability_id: str, acquisition_id: str,
            field: str, entity_field: str, unit: str, analysis_id: str, parameters: dict[str, Any] = {}) -> dict[str, Any]:
        """Execute only an accepted, currently qualified pinned mean on owned source rows."""
        from src.oncolab.reusable import resolve_reusable_method
        from src.science.reusable import extract_mean_input
        from src.science.qualification import recover_environment_inputs, record_reference
        from src.science.sandbox import validate_sandbox_candidate
        runtime = ctx.deps.runtime; owner = ctx.deps.block_id
        runtime.claim(owner, "tool", runtime.max_tool_calls)
        if parameters: raise ValueError("qualified mean has no parameters")
        candidate, proofs, scope = resolve_reusable_method(runtime, owner, capability_id)
        source = runtime.resolve_acquisition(owner, acquisition_id)
        values, lineage = extract_mean_input(source, field, entity_field, unit)
        basis = runtime.verification_environment_provider()
        environment = proofs[RecordKind.ENVIRONMENT_QUALIFICATION].payload
        identity = environment["runtime_identity"]
        if identity["python_sha256"] != basis["interpreter_sha256"] or identity["stdlib_sha256"] != basis["stdlib_sha256"]:
            raise ValueError("qualified runtime constraints changed")
        original, inputs = recover_environment_inputs(runtime.repository.store, environment["lock_reference"], runtime_identity=identity)
        request = original.request.model_copy(update={"requested_ref": original.receipt.commit_sha, "input_json": values})
        fresh = await runtime.execute_external(owner, request, recovery_inputs=inputs)
        if runtime.verification_environment_provider()["stdlib_sha256"] != identity["stdlib_sha256"]:
            raise ValueError("runtime changed during reusable execution")
        measurement = validate_sandbox_candidate(fresh, analysis_id)
        measurement = measurement.model_copy(update={"source_refs": (fresh.candidate_id, acquisition_id),
            "diagnostics": {**measurement.diagnostics, "reusable_method": capability_id, "qualified_candidate": candidate.candidate_id,
                "scope_sha256": content_hash(scope), "source_lineage": lineage,
                "qualification_references": [record_reference(r) for r in proofs.values()]},
            "limitations": ("Descriptive mean of the retained complete source slice; no population or oncology inference.",)})
        runtime.measurements[(owner, analysis_id)] = measurement
        current = runtime.research_state.get(owner)
        runtime.persist_state(current.add_measurement(measurement))
        runtime.repository.record_measurement(measurement, owner)
        runtime.index_receipt("researcher", "execute", block_id=owner, selected_id=capability_id)
        runtime.append_event(owner, "ReusableMethodValidated", {"capability_id": capability_id, "analysis_id": analysis_id,
            "candidate_id": fresh.candidate_id, "source_acquisition": acquisition_id, "scope_sha256": content_hash(scope)})
        return measurement.model_dump(mode="json")

    @agent.tool
    async def declare_method_reference(ctx: RunContext[Any], candidate_id: str, scope: dict[str, Any],
            source_artifact_id: str, licence_artifact_id: str) -> dict[str, Any]:
        """Predeclare fixed mean qualification from owned pinned upstream material."""
        from src.science.qualification import declare_mean_reference, record_reference
        runtime = ctx.deps.runtime; owner = ctx.deps.block_id
        runtime.claim(owner, "tool", runtime.max_tool_calls)
        store = runtime.repository.store
        candidate = next((r for r in store.records(kind=RecordKind.SANDBOX_CANDIDATE, block_id=owner) if r.record_id == candidate_id), None)
        if candidate is None: raise ValueError("reference candidate must belong to this block")
        refs = []
        for identity in (source_artifact_id, licence_artifact_id):
            runtime.repository.resolve_scientific_artifact(owner, identity)
            refs.append(record_reference(next(r for r in store.records(kind=RecordKind.SCIENTIFIC_ARTIFACT, block_id=owner) if r.record_id == identity)))
        declaration = declare_mean_reference(store, candidate_id, scope, *refs)
        return {"declaration_reference": record_reference(declaration), "cases": declaration.payload["cases"], "authority": "qualification_only"}

    @agent.tool
    async def validate_method_reference(ctx: RunContext[Any], declaration_seq: int, comparison_seqs: list[int]) -> dict[str, Any]:
        """Resolve controlled upstream/candidate comparisons; no flags or labels grant evidence."""
        from src.science.qualification import record_reference, retain_reference_validation
        runtime = ctx.deps.runtime; owner = ctx.deps.block_id
        runtime.claim(owner, "tool", runtime.max_tool_calls)
        if not 1 <= len(comparison_seqs) <= 20 or len(set(comparison_seqs)) != len(comparison_seqs):
            raise ValueError("bounded unique comparisons required")
        store = runtime.repository.store
        declaration = store.record_at(declaration_seq)
        if declaration is None or not any(r.record_id == declaration.payload.get("candidate_id") for r in store.records(kind=RecordKind.SANDBOX_CANDIDATE, block_id=owner)):
            raise ValueError("reference declaration must resolve this block's candidate")
        observations = [store.record_at(seq) for seq in comparison_seqs]
        if any(r is None for r in observations): raise ValueError("unresolved comparison")
        proof = retain_reference_validation(store, record_reference(declaration), [record_reference(r) for r in observations])
        return {"reference_validation": record_reference(proof), "status": proof.payload["status"], "results": proof.payload["results"]}

    @agent.tool
    async def qualify_method_environment(ctx: RunContext[Any], candidate_id: str, scope: dict[str, Any],
            archive_artifact_id: str) -> dict[str, Any]:
        """Restore the supported pinned stdlib-only method from exact retained bytes."""
        import hashlib
        import platform
        from pathlib import Path
        from src.science.qualification import (declare_environment_lock, recover_environment_inputs,
            retain_environment_qualification, record_reference)
        runtime = ctx.deps.runtime; owner = ctx.deps.block_id
        runtime.claim(owner, "sandbox", runtime.max_sandbox_calls)
        store = runtime.repository.store
        archive = next((r for r in store.records(kind=RecordKind.SCIENTIFIC_ARTIFACT) if r.record_id == archive_artifact_id), None)
        if archive is None: raise ValueError("owned recoverable archive required")
        basis = runtime.verification_environment_provider()
        identity = {"python_version": platform.python_version(), "python_sha256": basis["interpreter_sha256"],
            "stdlib_sha256": basis["stdlib_sha256"], "platform": platform.platform(),
            "installer": hashlib.sha256(Path(__file__).resolve().parents[2].joinpath("science/prepare_exec.py").read_bytes()).hexdigest()}
        lock = declare_environment_lock(store, candidate_id, scope, record_reference(archive), runtime_identity=identity)
        candidate, inputs = recover_environment_inputs(store, record_reference(lock), runtime_identity=identity)
        try:
            fresh = await runtime.execute_external(owner, candidate.request.model_copy(update={"requested_ref": candidate.receipt.commit_sha}), recovery_inputs=inputs)
            if runtime.verification_environment_provider()["stdlib_sha256"] != identity["stdlib_sha256"]:
                raise RuntimeError("standard library changed during recovery")
        except Exception as error:
            from src.persistence.records import StoredRecord
            from uuid import uuid4
            failure = store.append(StoredRecord(kind=RecordKind.SERVICE_EVENT, record_id=uuid4().hex, block_id=owner,
                payload={"event_type": "EnvironmentRecoveryFailure", "operational_only": True, "error_type": type(error).__name__,
                    "detail": str(error), "lock_reference": record_reference(lock)}))
            proof = retain_environment_qualification(store, record_reference(lock), None, runtime_identity=identity,
                failure_reference=record_reference(failure))
        else:
            saved = next(r for r in store.records(kind=RecordKind.SANDBOX_CANDIDATE, block_id=owner) if r.record_id == fresh.candidate_id)
            proof = retain_environment_qualification(store, record_reference(lock), record_reference(saved), runtime_identity=identity)
        return {"environment_qualification": record_reference(proof), "status": proof.payload["status"], "limitations": proof.payload["limitations"]}

    @agent.tool
    async def generate_representation_candidates(ctx: RunContext[Any], need: dict[str, Any],
            acquisition_ids: list[str], artifact_ids: list[str] = [], limit: int = 20) -> dict[str, Any]:
        """Source/schema-backed alternatives; metadata and derivability do not grant readiness."""
        from src.sources.representation import RepresentationNeed, representation_alternatives
        runtime = ctx.deps.runtime; block_id = ctx.deps.block_id
        runtime.claim(block_id, "tool", runtime.max_tool_calls)
        if len(acquisition_ids) > 20 or len(artifact_ids) > 20 or len(set(acquisition_ids)) != len(acquisition_ids) or len(set(artifact_ids)) != len(artifact_ids):
            raise ValueError("bounded unique owned asset identities required")
        result = representation_alternatives([runtime.resolve_acquisition(block_id, value) for value in acquisition_ids],
            [runtime.repository.resolve_scientific_artifact(block_id, value) for value in artifact_ids], RepresentationNeed.model_validate(need), limit=limit)
        from uuid import uuid4
        identity = str(uuid4())
        runtime.repository.record_immutable(RecordKind.METHOD_CANDIDATES, identity, {**result, "kind": "representations"}, block_id)
        return {**result, "receipt_id": identity}

    @agent.tool
    async def transform_gdc_representation(ctx: RunContext[Any], operation: str, acquisition_ids: list[str] = [],
            artifact_id: str | None = None, representation: str | None = None, column: str = "tpm_unstranded", gene_symbols: list[str] = []) -> dict[str, Any]:
        """Fixed source parsers/cohort/one-to-one join; owned lineage retained atomically."""
        from src.science.representation import parse_gdc_table, derive_gdc_clinical, join_gdc_case_inputs, assemble_gdc_expression
        runtime = ctx.deps.runtime; block_id = ctx.deps.block_id
        runtime.claim(block_id, "tool", runtime.max_tool_calls)
        if len(acquisition_ids) > 21 or len(set(acquisition_ids)) != len(acquisition_ids): raise ValueError("bounded unique owned inputs required")
        if gene_symbols and operation != "parse_gdc_table": raise ValueError("gene panel belongs only to the mutation table parser")
        records = [runtime.resolve_acquisition(block_id, value).model_copy(deep=True) for value in acquisition_ids]
        if operation == "parse_gdc_table" and artifact_id and not records:
            function, inputs = parse_gdc_table, (runtime.repository.resolve_scientific_artifact(block_id, artifact_id).model_copy(deep=True), representation, tuple(gene_symbols))
        elif operation == "derive_gdc_clinical" and len(records) == 1 and not artifact_id:
            function, inputs = derive_gdc_clinical, (records[0], block_id, representation)
        elif operation == "join_gdc_case_inputs" and len(records) == 2 and not artifact_id:
            function, inputs = join_gdc_case_inputs, (*records, block_id)
        elif operation == "assemble_gdc_expression" and 2 <= len(records) <= 21 and not artifact_id:
            function, inputs = assemble_gdc_expression, (tuple(records[:-1]), records[-1], block_id, column)
        else: raise ValueError("unsupported transform or input cardinality")
        from uuid import uuid4
        call_id = str(uuid4()); capability = "transform.gdc-tabular"
        runtime.index_receipt("researcher", "execute", block_id=block_id, selected_id=capability)
        runtime.append_event(block_id, "CapabilityInvocation", {"invocation_id": call_id,
            "capability_id": capability, "operation": operation, "acquisition_ids": acquisition_ids, "artifact_id": artifact_id})
        try:
            record, receipt = await runtime.heavy_operation(block_id, function, *inputs)
            with runtime.repository.store.transaction():
                runtime.retain_acquisition(block_id, record)
                runtime.repository.record_immutable(RecordKind.REPRESENTATION_PARSE, record.acquisition_id, receipt, block_id)
        except BaseException as error:
            runtime.append_event(block_id, "CapabilityFailure", {"invocation_id": call_id,
                "capability_id": capability, "error_type": type(error).__name__})
            raise
        runtime.append_event(block_id, "CapabilityResult", {"invocation_id": call_id,
            "capability_id": capability, "operation": operation, "acquisition_id": record.acquisition_id})
        return {"acquisition_id": record.acquisition_id, "records": record.records, "receipt": receipt.model_dump(mode="json")}

    @agent.tool
    async def parse_gdc_star_counts(ctx: RunContext[Any], artifact_id: str, gene_ids: list[str]) -> dict[str, Any]:
        """Parse selected exact gene IDs from an owned open GDC STAR Counts artifact."""
        from uuid import uuid4
        from src.science.representation import parse_gdc_star_counts as parse
        runtime=ctx.deps.runtime;block_id=ctx.deps.block_id
        if runtime.repository is None: raise ValueError("source parsing requires durable storage")
        runtime.claim(block_id,"tool",runtime.max_tool_calls)
        artifact=runtime.repository.resolve_scientific_artifact(block_id,artifact_id)
        call_id=str(uuid4());capability="transform.gdc-star-counts"
        runtime.index_receipt("researcher","execute",block_id=block_id,selected_id=capability)
        runtime.append_event(block_id,"CapabilityInvocation",{"invocation_id":call_id,"capability_id":capability,"artifact_id":artifact_id})
        try:
            record,receipt=await runtime.heavy_operation(block_id,parse,artifact.model_copy(deep=True),tuple(gene_ids))
            with runtime.repository.store.transaction():
                runtime.retain_acquisition(block_id,record)
                runtime.repository.record_immutable(RecordKind.REPRESENTATION_PARSE,record.acquisition_id,receipt,block_id)
        except Exception as error:
            runtime.append_event(block_id,"CapabilityFailure",{"invocation_id":call_id,"capability_id":capability,"error_type":type(error).__name__})
            raise
        runtime.append_event(block_id,"CapabilityResult",{"invocation_id":call_id,"capability_id":capability,"acquisition_id":record.acquisition_id,
            "input_artifact_id":artifact_id,"parser_version":receipt.parser_version,"selected_rows":len(record.records),"missing_gene_ids":receipt.missing_gene_ids})
        try: state=runtime.research_state.get(block_id)
        except KeyError: state=runtime.research_state.start(block_id,runtime.manager.block(block_id).objective)
        runtime.persist_state(state.append("acquisitions",StateFragment(fragment_id=record.acquisition_id,kind="gene_summary",
            summary="Source-bound selected genes in one STAR Counts file; sample/cohort linkage remains unknown.",
            provenance=(artifact_id,record.acquisition_id),details=receipt.model_dump(mode="json"))))
        return {"acquisition_id":record.acquisition_id,"receipt":receipt.model_dump(mode="json"),"records":record.records}

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
                                  test_plan:dict[str,Any]|None=None,followup_id:str|None=None)->dict[str,Any]:
        """Complete-row Pearson or OLS over owned retained inputs with explicit entity/design contract."""
        runtime=ctx.deps.runtime;block_id=ctx.deps.block_id
        runtime.claim(block_id,"tool",runtime.max_tool_calls)
        record=runtime.resolve_acquisition(block_id,acquisition_id)
        spec=AnalysisSpec(analysis_id=analysis_id,question=question,population=population,estimand=estimand,method=method,
            variables=tuple(fields),fields=fields,entity_field=entity_field,entity_unit=entity_unit,design=design,
            transformations=transformations,source_refs=(acquisition_id,),replication_id=replication_id,
            test_plan=HypothesisTestPlan.model_validate(test_plan) if test_plan is not None else None)
        from src.runtime.pydantic_ai.followup_tools import prepare_followup,retain_followup
        prepared=prepare_followup(runtime,block_id,followup_id,record,spec) if followup_id else None
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
            if prepared: retain_followup(runtime,prepared,record,stage=stage,failure_type=type(error).__name__)
            runtime.append_event(block_id,"CapabilityFailure",{"invocation_id":call_id,"capability_id":capability,"error_type":type(error).__name__, "scientific_invalid":invalid})
            raise
        runtime.measurements[(block_id,analysis_id)]=result
        try:state=runtime.research_state.get(block_id)
        except KeyError:state=runtime.research_state.start(block_id,runtime.manager.block(block_id).objective)
        runtime.persist_state(state.add_measurement(result))
        followup_result=None
        if runtime.repository is not None:
            with runtime.repository.store.transaction():
                runtime.repository.record_measurement(result,block_id)
                retain(attempt.model_copy(update={"stage":"completed",
                    "outcome":result.diagnostics.get("hypothesis_test", {}).get("outcome", "unknown"),
                    "measurement_reference":ExecutionReference(kind="measurement", value=analysis_id,
                        sha256=content_hash(result.model_dump(mode="json")), block_id=block_id)}))
                if prepared: followup_result=retain_followup(runtime,prepared,record,measurement=result)
        runtime.append_event(block_id,"ScienceMeasurement",{"analysis_id":analysis_id,"method":method,"analysis_key":result.analysis_key})
        runtime.append_event(block_id,"CapabilityResult",{"invocation_id":call_id,"capability_id":capability,"analysis_id":analysis_id,"origin":"source"})
        runtime.verification(block_id,capability,analysis_id,"measurement",result,"Paired complete-row association over stored source slice; assumptions and population representativeness not established.")
        return result.model_dump(mode="json") | ({"followup":followup_result.model_dump(mode="json")} if followup_result else {})
