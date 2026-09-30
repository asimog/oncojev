"""Immutable, provider-agnostic state owned by one JevBlock."""

import hashlib
import json
from typing import Any

from pydantic import BaseModel, Field

from src.science.models import MeasuredResult


class StateFragment(BaseModel, frozen=True):
    fragment_id: str
    kind: str
    summary: str
    provenance: tuple[str, ...] = Field(min_length=1)


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
        return self.model_copy(update={"evidence_ids": (*self.evidence_ids, evidence_id)})


class ProjectionSpec(BaseModel, frozen=True):
    projection_name: str
    candidate_id: str
    version: str = "1"


class JevProjection(BaseModel, frozen=True):
    projection_id: str
    payload: dict[str, Any]
    provenance: tuple[str, ...]


def project_state(state: ResearchState, spec: ProjectionSpec) -> JevProjection:
    """Produce a bounded JSON-only semantic view; never pass raw acquisitions or shell output."""
    payload = {
        "objective": state.objective,
        "candidate": next((fragment.summary for fragment in state.candidates if fragment.fragment_id == spec.candidate_id), spec.candidate_id),
        "observations": [fragment.summary for fragment in state.observations],
        "measurements": [{"analysis_id": item.analysis_id, "values": item.values} for item in state.measurements],
        "uncertainties": [fragment.summary for fragment in state.uncertainties],
        "prior_actions": [fragment.kind for fragment in state.prior_actions],
    }
    canonical = json.dumps({"spec": spec.model_dump(mode="json"), "state": payload}, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode()).hexdigest()[:16]
    return JevProjection(projection_id=f"{spec.projection_name}-v{spec.version}-{digest}", payload=payload, provenance=("research-state-v1", spec.projection_name))


class ResearchStateStore:
    def __init__(self) -> None: self._states: dict[str, ResearchState] = {}
    def start(self, block_id: str, objective: str) -> ResearchState:
        state = ResearchState(block_id=block_id, objective=objective); self._states[block_id] = state; return state
    def get(self, block_id: str) -> ResearchState: return self._states[block_id]
    def put(self, state: ResearchState) -> ResearchState: self._states[state.block_id] = state; return state
