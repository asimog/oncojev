"""Bounded operational change packets derived only from persisted references."""
from datetime import datetime
from pydantic import BaseModel, Field
from src.memory.models import MemoryReference
from src.persistence.records import RecordKind
from src.provenance import content_hash


class BlockDelta(BaseModel, frozen=True):
    version: str = "block-delta-v1"
    block_id: str
    run_id: str
    start_sequence: int
    end_sequence: int
    references: dict[str, tuple[MemoryReference, ...]] = Field(default_factory=dict)
    omitted: dict[str, int] = Field(default_factory=dict)
    resources: dict = Field(default_factory=dict)
    limitations: tuple[str, ...] = ()


def build_delta(store, block, run_id, start_sequence, finished_at: datetime, *, researcher_seconds=None, director_seconds=None, idle_seconds=None):
    records = tuple(r for r in store.records(block_id=block.block_id) if r.seq >= start_sequence)
    groups = {}
    for record in records:
        category = {RecordKind.EVIDENCE: "evidence", RecordKind.MEASUREMENT: "measurements",
                    RecordKind.METHOD_CANDIDATES: "method_alternatives",
                    RecordKind.REPRESENTATION_PARSE: "parsed_representations",
                    RecordKind.JEV_OUTPUT: "semantic_measurements", RecordKind.STATE_REVISION: "state_changes",
                    RecordKind.SCIENTIFIC_ATTEMPT: "scientific_attempts", RecordKind.LITERATURE_CONTEXT: "literature_contexts",
                    RecordKind.FOLLOWUP_PLAN:"followup_plans",RecordKind.FOLLOWUP_RESULT:"scientific_followups"}.get(record.kind)
        if record.kind is RecordKind.LEDGER_EVENT:
            category = {"ReasonerOutput": "hypotheses", "ScientificNegativeFinding": "scientific_negatives",
                        "UncertaintyRecorded": "uncertainties", "ExplicitResolution": "resolutions",
                        "ScopeEscalationRequested": "continuations", "CapabilityFailure": "operational_blockers",
                        "ResearcherRunFailed": "operational_blockers", "CapabilityDemand": "capability_demand",
                        "CapabilityGap": "capability_gaps", "CrossBlockRelationCandidate": "relation_candidates"}.get(record.payload["event_type"])
        if category:
            reference = MemoryReference(kind=record.kind, record_id=record.record_id,
                seq=record.seq, block_id=record.block_id, sha256=content_hash(record.payload))
            groups.setdefault(category, []).append(reference)
            if record.kind is RecordKind.LEDGER_EVENT and record.payload["event_type"] == "ReasonerOutput" and record.payload["payload"].get("uncertainty"):
                groups.setdefault("uncertainties", []).append(reference)
    events = [r.payload for r in records if r.kind is RecordKind.LEDGER_EVENT]
    execution_events = [e for e in events if e["event_type"] in
                        {"InstalledScienceResourceReceipt", "CoderExecutionReceipt", "ScientificResourceReceipt"}]
    executions = []
    for event in execution_events:
        detail = event["payload"]
        executions.extend(detail.get("executions", [detail]))
    cpu_observed = []
    for detail in executions:
        stats = dict(line.split() for line in detail.get("cpu_stat", "").splitlines() if len(line.split()) == 2)
        if "usage_usec" in stats:
            cpu_observed.append(int(stats["usage_usec"]) / 1_000_000)
        elif detail.get("unit_observation", {}).get("CPUUsageNSec", "").isdigit():
            cpu_observed.append(int(detail["unit_observation"]["CPUUsageNSec"]) / 1_000_000_000)
    workspace_observed = [d["block_workspace_after_bytes"] for d in executions if "block_workspace_after_bytes" in d]
    workspace_peaks = [d["block_workspace_before_bytes"] + d["workspace_peak_allocated_bytes"]
                       for d in executions if "block_workspace_before_bytes" in d and "workspace_peak_allocated_bytes" in d]
    elapsed = max(0, (finished_at - block.started_at).total_seconds())
    allowance = block.start.allocation.seconds
    return BlockDelta(block_id=block.block_id, run_id=run_id, start_sequence=start_sequence,
        end_sequence=store.high_water(), references={k: tuple(v[:20]) for k,v in groups.items()},
        omitted={k: max(0, len(v)-20) for k,v in groups.items()}, resources={
            "allocated_seconds": allowance, "actual_elapsed_seconds": elapsed,
            "unused_allowance_seconds": max(0, allowance-elapsed), "reason_for_terminal_state": block.termination_reason,
            "researcher_active_seconds": researcher_seconds, "director_turn_seconds": director_seconds,
            "director_idle_wait_seconds": idle_seconds,
            "downloaded_bytes": sum(e["payload"].get("bytes",0) for e in events if e["event_type"] == "DownloadUsage"),
            "heavy_lease_acquisitions": sum(e["event_type"] == "HeavyExecutionLease" for e in events),
            "scientific_executions": sum(e["event_type"] == "ScienceMeasurement" for e in events),
            "resource_limit_failures": sum(e["event_type"] in {"WorkNotStarted", "ResourceRejected"} for e in events),
            "workspace_observed_bytes": workspace_observed[-1] if workspace_observed else None,
            "workspace_peak_bytes": max(workspace_peaks) if workspace_peaks else None,
            "cpu_seconds": sum(cpu_observed) if executions and len(cpu_observed) == len(executions) else None,
            "cpu_observed_seconds": sum(cpu_observed) if cpu_observed else None,
            "measured_process_families": len(cpu_observed), "process_families": len(executions)},
        limitations=("Turn and transport durations are wall time, not CPU measurements.",
                     "Only explicit negative/resolution events appear; missing entries are not negatives or resolutions.",
                     "Workspace peaks are sampled allocated-byte lower bounds; missing CPU counters remain unknown. Exact registry/history pins follow H5."))
