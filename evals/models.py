"""Evaluation contracts.

A report compares observable outcomes across capability conditions. It carries
no `best`/`winner` field: which condition is preferable is a research question,
not a hardcoded expectation.
"""

from src.oncolab.utility import UtilityCondition as EvaluationCondition

from pydantic import BaseModel, Field
from src.block.models import CycleStatus


class ConditionMetrics(BaseModel, frozen=True):
    condition: EvaluationCondition
    blocks: int = 0
    measurements: int = 0
    evidence: int = 0
    deterministic_evidence: bool = True
    jev_executions: int = 0
    reasoner_outputs: int = 0
    dossiers: int = 0
    hypotheses: int = 0
    proposed_new_blocks: int = 0
    has_preferred_continuation: bool = False
    records: int = 0
    source_bound_evidence: int = 0
    verified_replications: int = 0
    invalid_designs: int = 0
    memory_retrievals: int = 0
    uncertainty_resolutions: int | None = None
    provider_cost: float | None = None
    downloaded_bytes: int | None = None
    unique_analysis_outcomes: int | None = None
    declared_replication_outcomes: int = 0
    jev_failures: int = 0
    completed_blocks: int = 0
    elapsed_seconds: float = 0.0
    status: CycleStatus = CycleStatus.COMPLETE
    error_type: str | None = None
    failed_cycles: int = 0
    incomplete_cycles: int = 0
    cycles: int = 0


class EvaluationReport(BaseModel, frozen=True):
    direction: str
    mode: str
    conditions: tuple[ConditionMetrics, ...] = Field(min_length=1)
    provenance: tuple[str, ...] = ("evals-v2-live-autonomous",)
