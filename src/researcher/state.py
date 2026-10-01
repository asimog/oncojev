"""Immutable, provider-agnostic state owned by one JevBlock."""

from typing import Any

from pydantic import BaseModel, Field

from src.science.models import MeasuredResult
from src.provenance import canonical_bytes, content_hash


class StateFragment(BaseModel, frozen=True):
    fragment_id: str
    kind: str
    summary: str
    provenance: tuple[str, ...] = Field(min_length=1)
    details: dict[str, Any] = Field(default_factory=dict)


class ResearchState(BaseModel, frozen=True):
    block_id: str
    objective: str
    observations: tuple[StateFragment, ...] = ()
    acquisitions: tuple[StateFragment, ...] = ()
    measurements: tuple[MeasuredResult, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    candidates: tuple[StateFragment, ...] = ()
    uncertainties: tuple[StateFragment, ...] = ()
    prior_actions: tuple[StateFragment, ...] = ()
    provenance: tuple[str, ...] = ("research-state-v1",)

    def append(self, field: str, fragment: StateFragment) -> "ResearchState":
        return self.model_copy(update={field: (*getattr(self, field), fragment)})

    def add_measurement(self, result: MeasuredResult) -> "ResearchState":
        return self.model_copy(update={"measurements": (*self.measurements, result)})

    def add_evidence(self, evidence_id: str) -> "ResearchState":
        return self if evidence_id in self.evidence_ids else self.model_copy(update={"evidence_ids": (*self.evidence_ids, evidence_id)})


class ProjectionSpec(BaseModel, frozen=True):
    projection_name: str
    candidate_id: str
    version: str = "2"
    max_items: int = Field(default=20, ge=1, le=100)
    max_payload_bytes: int = Field(default=65536, ge=4096, le=1000000)
    max_text_chars: int = Field(default=2000, ge=128, le=16000)


class JevProjection(BaseModel, frozen=True):
    projection_id: str
    payload: dict[str, Any]
    provenance: tuple[str, ...]
    payload_sha256: str
    spec: ProjectionSpec


def project_state(state: ResearchState, spec: ProjectionSpec) -> JevProjection:
    """Produce a bounded JSON-only semantic view; never pass raw acquisitions or shell output."""
    def fragments(items):
        return [{"fragment_id": f.fragment_id, "kind": f.kind, "summary": f.summary[:spec.max_text_chars],
                 "summary_truncated": len(f.summary) > spec.max_text_chars,
                 "provenance": f.provenance, "details": f.details} for f in items[-spec.max_items:]]

    candidate = next((f for f in state.candidates if f.fragment_id == spec.candidate_id), None)
    payload = {"projection_version": spec.version, "objective": state.objective[:spec.max_text_chars],
               "objective_truncated": len(state.objective) > spec.max_text_chars,
               "candidate_id": spec.candidate_id, "candidate": (candidate.summary if candidate else spec.candidate_id)[:spec.max_text_chars],
               "candidate_truncated": bool(candidate and len(candidate.summary) > spec.max_text_chars),
               "observations": fragments(state.observations), "acquisition_summaries": fragments(state.acquisitions),
               "measurements": [{"analysis_id": m.analysis_id, "values": m.values, "origin": m.origin,
                                  "source_refs": m.source_refs, "input_sha256": m.input_sha256,
                                  "provenance": m.provenance, "limitations": m.limitations, "interpretation":m.interpretation, "analysis_key":m.analysis_key, "diagnostics":m.diagnostics} for m in state.measurements[-spec.max_items:]],
               "evidence_refs": list(state.evidence_ids[-spec.max_items:]),
               "uncertainties": fragments(state.uncertainties), "prior_actions": fragments(state.prior_actions),
               "omitted": {}}
    inputs = {"observations": state.observations, "acquisition_summaries": state.acquisitions,
              "measurements": state.measurements, "evidence_refs": state.evidence_ids,
              "uncertainties": state.uncertainties, "prior_actions": state.prior_actions}
    payload["omitted"] = {key: max(0, len(items) - spec.max_items) for key, items in inputs.items()}
    # Omit whole items rather than altering measured values or implying zero.
    while len(canonical_bytes(payload)) > spec.max_payload_bytes:
        key = max(inputs, key=lambda key: len(canonical_bytes(payload[key])) if payload[key] else 0)
        if not payload[key]:
            raise ValueError("mandatory projection context exceeds configured byte bound")
        payload[key].pop(0)
        payload["omitted"][key] += 1
    digest = content_hash({"spec": spec.model_dump(mode="json"), "state": payload})
    return JevProjection(projection_id=f"{spec.projection_name}-v{spec.version}-{digest[:16]}", payload=payload,
                         payload_sha256=content_hash(payload), spec=spec,
                         provenance=("research-state-v2", spec.projection_name))


class ResearchStateStore:
    def __init__(self) -> None: self._states: dict[str, ResearchState] = {}
    def start(self, block_id: str, objective: str) -> ResearchState:
        state = ResearchState(block_id=block_id, objective=objective); self._states[block_id] = state; return state
    def get(self, block_id: str) -> ResearchState: return self._states[block_id]
    def put(self, state: ResearchState) -> ResearchState: self._states[state.block_id] = state; return state
