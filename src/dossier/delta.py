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
                    RecordKind.JEV_OUTPUT: "semantic_measurements", RecordKind.STATE_REVISION: "state_changes",
                    RecordKind.SCIENTIFIC_ATTEMPT: "scientific_attempts"}.get(record.kind)
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
            "workspace_observed_bytes": None, "workspace_peak_bytes": None, "cpu_seconds": None},
        limitations=("Turn and transport durations are wall time, not CPU measurements.",
                     "Only explicit negative/resolution events appear; missing entries are not negatives or resolutions.",
                     "Workspace and CPU measurements are unavailable; exact registry/history pins follow H5."))
