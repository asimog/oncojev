"""Typed transport for installed scientific work under the Linux governor.

The service owns inputs, receipts and persistence. Workers receive JSON values
for a fixed set of operations, never callables, credentials or store handles.
"""
from dataclasses import dataclass, field, replace
import json
from pathlib import Path
import sys
from uuid import uuid4

from src.runtime.process import ProcessLimits, run_owned_command, workspace_bytes
from src.runtime.resources import ResourceRejected
from src.science.models import InvalidAnalysis, MeasuredResult
from src.sources.models import AcquisitionRecord
from src.science.representation import RepresentationParseReceipt, TabularTransformReceipt
from src.visualization.models import FigureArtifact


OPERATIONS = {
    ("src.science.execution", "execute"),
    ("src.science.execution", "execute_source"),
    ("src.science.execution", "measure_acquisition"),
    ("src.science.representation", "parse_gdc_star_counts"),
    ("src.visualization.service", "line_figure"),
    *(('src.science.representation', name) for name in ('parse_gdc_table', 'derive_gdc_clinical', 'join_gdc_case_inputs', 'assemble_gdc_expression')),
}


def operation_name(operation):
    key = (getattr(operation, "__module__", ""), getattr(operation, "__name__", ""))
    return key[1] if key in OPERATIONS else None


def decode_result(name, value):
    if name == "parse_gdc_star_counts":
        return AcquisitionRecord.model_validate(value[0]), RepresentationParseReceipt.model_validate(value[1])
    if name in {'parse_gdc_table', 'derive_gdc_clinical', 'join_gdc_case_inputs', 'assemble_gdc_expression'}:
        return AcquisitionRecord.model_validate(value[0]), TabularTransformReceipt.model_validate(value[1])
    if name == "line_figure":
        return FigureArtifact.model_validate(value)
    return MeasuredResult.model_validate(value)


@dataclass
class InstalledScienceRunner:
    application: Path
    limits: ProcessLimits
    executions: list[dict] = field(default_factory=list)

    def run(self, workspace, operation, *inputs):
        name = operation_name(operation)
        if name is None:
            raise ValueError("unsupported installed scientific operation")
        workspace = Path(workspace).resolve()
        workspace.mkdir(parents=True, exist_ok=True)
        if (workspace / "installed-science").is_symlink():
            raise ResourceRejected("installed_science_workspace_link", 0)
        block_before = workspace_bytes(workspace)
        remaining = self.limits.workspace_bytes - block_before
        def encode(value):
            if hasattr(value, "model_dump"): return value.model_dump(mode="json")
            if isinstance(value, (tuple, list)): return [encode(v) for v in value]
            if isinstance(value, dict): return {key: encode(v) for key, v in value.items()}
            return value
        encoded = json.dumps({"operation": name, "inputs": encode(inputs)},
            allow_nan=False).encode("utf-8")
        if remaining <= len(encoded) + 131072:
            raise ResourceRejected("installed_science_workspace_capacity", 0)
        root = workspace / "installed-science" / uuid4().hex
        root.mkdir(parents=True)
        (root / "request.json").write_bytes(encoded)
        environment = {
            "PATH": str(Path(sys.executable).parent) + ":/usr/bin:/bin",
            "HOME": str(root), "TMPDIR": str(root), "MPLCONFIGDIR": str(root / "matplotlib"),
            "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1",
            "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
        }
        result = run_owned_command(root, [sys.executable, "-I",
            str(self.application / "src/science/installed_exec.py"), str(self.application), str(root)],
            environment, replace(self.limits, workspace_bytes=remaining))
        receipt = {**result.resources, "operation": name, "workspace": str(root),
                   "exit_code": result.exit_code, "operational_only": True,
                   "block_workspace_before_bytes": block_before,
                   "block_workspace_after_bytes": workspace_bytes(workspace)}
        self.executions.append(receipt)
        if (not receipt.get("kernel_controls_verified") or not receipt.get("cleanup_confirmed")
                or result.exit_code != 0):
            raise ResourceRejected("installed_science_execution_failed", 0)
        response = root / "result.json"
        if response.is_symlink() or not response.is_file() or response.stat().st_size > self.limits.output_bytes:
            raise ResourceRejected("installed_science_result_unavailable_or_exceeds_limit", 0)
        payload = json.loads(response.read_text(encoding="utf-8"))
        if payload.get("status") == "invalid":
            raise InvalidAnalysis(payload["error"])
        if payload.get("status") != "success":
            raise ResourceRejected("installed_science_result_invalid", 0)
        return decode_result(name, payload["value"])
