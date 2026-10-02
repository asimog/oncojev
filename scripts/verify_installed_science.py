"""Explicit native installed-Science qualification probes; no live providers."""
import asyncio
import base64
from dataclasses import replace
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import tempfile

from src.block.manager import BlockManager
from src.config.environment import process_settings
from src.dossier.delta import build_delta
from src.jev.client import DeterministicJevClient
from src.persistence.repository import ResearchRepository
from src.persistence.store import SqliteResearchStore
from src.reasoner.service import DeterministicReasoner
from src.runtime.paths import select_paths
from src.runtime.process import ProcessLimits
from src.runtime.pydantic_ai.contracts import HarnessRuntime
from src.runtime.resources import ResourceBusy, ResourceRejected
from src.science.execution import ScienceExecutor
from src.science.installed import InstalledScienceRunner
from src.science.models import AnalysisSpec, InvalidAnalysis
from src.science.representation import COLUMNS, parse_gdc_star_counts
from src.sources.models import AcquisitionRecord, ScientificArtifact
from src.visualization.service import line_figure


def verify_shutdown(application, root, limits, spec):
    """Exercise the same aggregate Runner shutdown used by AutonomousService."""
    from src.runtime.paths import RuntimePaths
    runtime = HarnessRuntime(BlockManager(), DeterministicJevClient(), ScienceExecutor(), DeterministicReasoner(), 1, 1)
    runtime.runtime_paths = RuntimePaths(root, root / "workspaces", root / "director")
    runtime.installed_science_runner = InstalledScienceRunner(application, limits)
    root.mkdir(parents=True)
    store = SqliteResearchStore(root / "shutdown.sqlite3")
    runtime.repository = ResearchRepository(store)
    block = runtime.manager.allocate("shutdown", "native drain", 300)
    runtime.repository.record_block(block)
    loop = asyncio.Runner()
    handles = []
    async def launch():
        handles.append(asyncio.create_task(runtime.heavy_operation(block.block_id, runtime.science.execute, spec)))
        while runtime.service_resources.heavy_owner is None:
            await asyncio.sleep(.01)
    loop.run(launch())
    assert runtime.service_resources.heavy_owner == block.block_id
    loop.close()
    assert handles[0].done() and handles[0].result().values["mean"] == 2.
    assert runtime.service_resources.heavy_owner is None
    assert runtime.installed_science_runner.executions[-1]["cleanup_confirmed"]
    from src.persistence.records import RecordKind
    assert any(r.payload.get("event_type") == "InstalledScienceResourceReceipt" for r in store.records(kind=RecordKind.LEDGER_EVENT))
    store.close()
    return runtime.installed_science_runner.executions[-1]


async def main():
    application = Path(__file__).resolve().parents[1]
    paths = select_paths(application, process_settings(application))
    paths.data.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="installed-proof-", dir=paths.data) as directory:
        root = Path(directory)
        store = SqliteResearchStore(root / "proof.sqlite3")
        runtime = HarnessRuntime(BlockManager(), DeterministicJevClient(), ScienceExecutor(),
                                 DeterministicReasoner(), 1, 1)
        runtime.repository = ResearchRepository(store)
        runtime.runtime_paths = replace(paths, data=root, workspaces=root / "workspaces", director=root / "director")
        from src.config.loader import load_runtime_config
        policy = load_runtime_config(application / "config/runtime.yaml", testing=paths.testing)
        limits = ProcessLimits(processes=policy.resources.max_science_processes,
            memory_mb=policy.sandbox.memory_mb, cpu=policy.sandbox.cpu,
            wall_seconds=policy.sandbox.timeout_seconds, workspace_bytes=policy.resources.max_workspace_bytes,
            minimum_free_disk_bytes=policy.resources.minimum_free_disk_bytes)
        runner = InstalledScienceRunner(application, limits)
        runtime.installed_science_runner = runner
        block = runtime.manager.allocate("native installed operations", "explicit qualification", 300)
        runtime.repository.record_block(block)
        spec = AnalysisSpec(analysis_id="summary", question="fixture", population="fixture", estimand="mean",
                            method="descriptive_summary", variables=("values",), inputs={"values": [1., 2., 3.]})
        result = await runtime.heavy_operation(block.block_id, runtime.science.execute, spec)
        assert result.values["mean"] == 2. and result.origin == "provided"
        record = AcquisitionRecord(source="fixture", request={}, origin="synthetic",
            records=tuple({"id": str(i), "x": i, "y": 2 * i} for i in range(1, 5)), provenance=("controlled native fixture",))
        result = await runtime.heavy_operation(block.block_id, runtime.science.measure_acquisition, record, "count", None)
        assert result.values == {"record_count": 4} and result.origin == "synthetic"
        paired = spec.model_copy(update={"analysis_id": "paired", "method": "pearson_correlation", "inputs": {},
            "source_refs": (record.acquisition_id,), "fields": {"x": "x", "y": "y"}, "entity_field": "id"})
        result = await runtime.heavy_operation(block.block_id, runtime.science.execute_source, record, paired)
        assert abs(result.values["correlation"] - 1.) < 1e-12 and result.origin == "synthetic"
        gene = "ENSG000001"
        data = ("\t".join(COLUMNS) + "\n" + "\t".join((gene, "GENE", "protein_coding", "1", "1", "1", "1", "1", "1")) + "\n").encode()
        metadata = {"file_id": "fixture", "access": "open", "data_format": "TSV",
                    "data_type": "Gene Expression Quantification", "analysis": {"workflow_type": "STAR - Counts"}}
        artifact = ScientificArtifact(block_id=block.block_id, source="gdc", request={"file_id": "fixture", "metadata": metadata},
            source_identity="fixture", content_base64=base64.b64encode(data).decode(), byte_sha256=hashlib.sha256(data).hexdigest(),
            size_bytes=len(data), format="tsv", provenance=("controlled parser fixture; not source evidence",))
        parsed, receipt = await runtime.heavy_operation(block.block_id, parse_gdc_star_counts, artifact, (gene,))
        assert parsed.records[0]["gene_id"] == gene and receipt.byte_sha256 == artifact.byte_sha256
        from src.science.representation import parse_gdc_table, derive_gdc_clinical, join_gdc_case_inputs, assemble_gdc_expression
        from src.sources.models import CoverageContract
        for modality, header, row, data_type, data_format in (
            ('mutation_events', 'Hugo_Symbol\tNCBI_Build\tChromosome\tStart_Position\tEnd_Position\tReference_Allele\tTumor_Seq_Allele2\tTumor_Sample_Barcode\tVariant_Classification', 'GENE\tGRCh38\t1\t10\t10\tA\tT\taliquot\tMissense_Mutation', 'Masked Somatic Mutation', 'MAF'),
            ('cnv_segments', 'GDC_Aliquot\tChromosome\tStart\tEnd\tNum_Probes\tSegment_Mean', 'aliquot\t1\t10\t20\t5\t-0.3', 'Copy Number Segment', 'TXT')):
            raw = (header + '\n' + row + '\n').encode()
            table = artifact.model_copy(update={'content_base64': base64.b64encode(raw).decode(), 'byte_sha256': hashlib.sha256(raw).hexdigest(),
                'size_bytes': len(raw), 'request': {'file_id': 'fixture', 'metadata': {'file_id': 'fixture', 'access': 'open', 'data_type': data_type, 'data_format': data_format}}})
            transformed, transform_receipt = await runtime.heavy_operation(block.block_id, parse_gdc_table, table, modality)
            assert len(transformed.records) == 1 and transform_receipt.input_references[0].value == artifact.artifact_id
        cases = AcquisitionRecord(source='gdc', origin='synthetic', request={}, records=({'case_id': 'case', 'demographic': {'vital_status': 'Dead', 'days_to_death': 20}},),
            provenance=('controlled schema fixture',), coverage=CoverageContract(endpoint='cases', requested_size=1, returned_rows=1, reported_total=1, id_field='case_id', unique_entities=1, ordering='fixture', complete=True))
        survival, _ = await runtime.heavy_operation(block.block_id, derive_gdc_clinical, cases, block.block_id, 'survival')
        assert survival.records[0]['time_days'] == 20 and survival.origin == 'synthetic'
        joined, _ = await runtime.heavy_operation(block.block_id, join_gdc_case_inputs, survival, survival, block.block_id)
        assert joined.records[0]['pair_complete']
        links = cases.model_copy(update={'records': ({'file_id': 'fixture', 'cases': [{'case_id': 'case', 'samples': [{'sample_id': 'sample', 'portions': [{'analytes': [{'aliquots': [{'aliquot_id': 'aliquot'}]}]}]}]}]},),
            'coverage': cases.coverage.model_copy(update={'endpoint': 'files', 'id_field': 'file_id'})})
        matrix, matrix_receipt = await runtime.heavy_operation(block.block_id, assemble_gdc_expression, (parsed,), links, block.block_id, 'tpm_unstranded')
        assert matrix.records[0]['gene_0'] == 1. and len(matrix_receipt.input_references) == 2
        figure = await runtime.heavy_operation(block.block_id, line_figure, "native", [1., 2.], [2., 4.])
        assert figure.media_type == "image/svg+xml" and figure.sha256
        try:
            await runtime.heavy_operation(block.block_id, runtime.science.execute, spec.model_copy(update={"inputs": {"values": [1.]}}))
        except InvalidAnalysis:
            pass
        else:
            raise AssertionError("invalid installed scientific input was accepted")
        # The real installed worker exceeds this cgroup while importing its
        # actual scientific dependencies. A service-side check cannot satisfy it.
        runner.limits = replace(limits, memory_mb=64)
        try:
            await runtime.heavy_operation(block.block_id, runtime.science.execute, spec)
        except ResourceRejected:
            pass
        else:
            raise AssertionError("installed worker escaped memory cgroup")
        assert runner.executions[-1]["unit_observation"]["Result"] == "oom-kill"
        assert runner.executions[-1]["cleanup_confirmed"] and runtime.service_resources.heavy_owner is None
        runner.limits = limits
        # Cancellation must drain the actual worker before releasing its lease.
        before = len(runner.executions)
        pending = asyncio.create_task(runtime.heavy_operation(block.block_id, runtime.science.execute, spec))
        while runtime.service_resources.heavy_owner is None and not pending.done():
            await asyncio.sleep(.01)
        pending.cancel()
        await asyncio.sleep(.02)
        assert not pending.done()
        try:
            async with runtime.service_resources.heavy("director"):
                raise AssertionError("Director scratch interrupted installed science")
        except ResourceBusy:
            pass
        assert (await pending).values["mean"] == 2.
        assert len(runner.executions) == before + 1 and runtime.service_resources.heavy_owner is None
        delta = build_delta(store, block, "native", 0, datetime.now(UTC))
        assert delta.resources["cpu_observed_seconds"] > 0 and delta.resources["workspace_peak_bytes"] > 0
        assert len(runtime.service_resources.execution_receipts) == len(runner.executions)
        # Previously retained work consumes the next operation's disk allowance.
        workspace = runtime.runtime_paths.workspaces / block.block_id
        runner.limits = replace(limits, workspace_bytes=1)
        try:
            await runtime.heavy_operation(block.block_id, runtime.science.execute, spec)
        except ResourceRejected:
            pass
        else:
            raise AssertionError("installed workspace capacity reset on next operation")
        assert workspace.is_dir() and figure.sha256
        shutdown_receipt = await asyncio.to_thread(verify_shutdown, application, root / "shutdown", limits, spec)
        print(json.dumps({"status": "passed", "scope": "native installed operations and resource/lease controls; fixture scientific inputs",
            "testing": paths.testing, "executions": runner.executions, "delta_resources": delta.resources,
            "shutdown_receipt": shutdown_receipt,
            "checks": {"statistics": True, "source_summary": True, "source_paired": True, "parser": True,
                       "figure": True, "invalid_input": True, "memory_cgroup": True, "cancellation_drain": True,
                       "director_exclusion": True, "retained_workspace_allowance": True, "aggregate_shutdown_drain": True, "tabular_modalities": True, "clinical_survival": True, "case_join": True, "expression_cohort": True}}))
        store.close()


if __name__ == "__main__":
    asyncio.run(main())
