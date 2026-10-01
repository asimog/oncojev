"""Deterministic dossier construction.

A dossier is a bounded summary assembled from an append-only ledger and the
block's deterministic state. It is provenance-bearing but is not evidence and
must never be treated as a measurement.
"""

from collections.abc import Sequence

from src.block.models import JevBlock, run_outcome
from src.dossier.models import JevBlockDossier
from src.ledger.events import LedgerEvent
from src.researcher.state import ResearchState


def _payloads(events: Sequence[LedgerEvent], event_type: str) -> list[dict]:
    return [event.payload for event in events if event.event_type == event_type]


def build_dossier(
    block: JevBlock,
    events: Sequence[LedgerEvent],
    state: ResearchState | None,
    termination_reason: str,
) -> JevBlockDossier:
    """Assemble one dossier from recorded events and immutable state."""
    evidence_ids = list(state.evidence_ids) if state is not None else []
    for payload in _payloads(events, "EvidenceAdmission"):
        evidence_id = payload.get("evidence_id")
        if isinstance(evidence_id, str) and evidence_id not in evidence_ids:
            evidence_ids.append(evidence_id)

    analyses = [str(payload.get("analysis_id")) for payload in _payloads(events, "ScienceMeasurement") if payload.get("analysis_id")]
    jev_questions = [str(q) for payload in _payloads(events, "JevExecution") for q in payload.get("question_ids", [])]
    frontier = [str(payload.get("action")) for payload in _payloads(events, "FrontierDecision") if payload.get("action")]

    hypotheses: list[str] = []
    within: list[str] = []
    beyond: list[str] = []
    uncertainties: list[str] = []
    for payload in _payloads(events, "ReasonerOutput"):
        if isinstance(payload.get("uncertainty"), str):
            uncertainties.append(payload["uncertainty"])
        for hypothesis in payload.get("hypotheses", []):
            statement = hypothesis.get("statement") if isinstance(hypothesis, dict) else None
            proposed = hypothesis.get("proposed_test") if isinstance(hypothesis, dict) else None
            if isinstance(statement, str):
                hypotheses.append(statement)
                if hypothesis.get("within_scope"):
                    within.append(str(proposed))
                else:
                    beyond.append(str(proposed))
    for payload in _payloads(events, "ScopeEscalationRequested"):
        if payload.get("proposed_test"):
            beyond.append(str(payload["proposed_test"]))

    resource_usage = {
        "jev_calls": len(_payloads(events, "JevExecution")),
        "reasoner_calls": len(_payloads(events, "ReasonerOutput")),
        "source_calls": len(_payloads(events, "CapabilityInvocation")),
        "sandbox_calls": len(_payloads(events, "GithubAcquisitionCompleted")),
        "evidence": len(evidence_ids),
    }
    for payload in _payloads(events, "ResourceAttempt"):
        name = payload.get("resource")
        if isinstance(name, str):
            resource_usage[f"{name}_attempts"] = max(resource_usage.get(f"{name}_attempts", 0), int(payload["attempt"]))

    preferred = next((item for item in within if item), "review unresolved block state")
    preferred_reason = (
        "Within-scope continuation proposed by the Reasoner and recorded in the ledger."
        if within
        else "No within-scope continuation was recorded; Director review is required."
    )
    return JevBlockDossier(
        lifecycle_status=block.status,
        run_outcome=run_outcome(events),
        operational_failures=tuple({"event_type": event.event_type, **event.payload} for event in events
                                   if event.event_type in {"ResearcherRunFailed", "DirectorRunFailed", "DirectorRunTruncated", "InterruptedBlockRecovered", "CycleFinalizationFailed"}),
        block_id=block.block_id,
        objective=block.objective,
        termination_reason=termination_reason,
        evidence_refs=tuple(evidence_ids),
        positive_findings=tuple(f"admitted evidence {evidence_id}" for evidence_id in evidence_ids),
        hypotheses=tuple(hypotheses),
        unresolved_uncertainties=tuple(dict.fromkeys(uncertainties)),
        important_jev_measurements=tuple(jev_questions),
        frontier_decisions=tuple(frontier),
        analyses_performed=tuple(analyses),
        resource_usage=resource_usage,
        recommended_next_blocks=tuple(dict.fromkeys(beyond)),
        preferred_continuation=preferred,
        preferred_continuation_reason=preferred_reason,
    )
