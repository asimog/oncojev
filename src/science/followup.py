"""Predeclared, model-conditional challenges to retained source-paired findings."""
import math
from typing import Annotated, Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field, model_validator
from src.provenance import ExecutionReference, content_hash, canonical_bytes
from src.science.models import AnalysisSpec, MeasuredResult, InvalidAnalysis
from src.sources.models import AcquisitionRecord


class FollowupPlan(BaseModel, frozen=True):
    version: Literal["source-followup-v1"] = "source-followup-v1"
    followup_id: str
    block_id: str
    comparison_id: str = Field(min_length=1, max_length=200)
    kind: Literal["independent_replication", "sensitivity"]
    baseline_attempt_id: str
    baseline_measurement: ExecutionReference
    baseline_input: ExecutionReference
    baseline_analysis: AnalysisSpec
    target_analysis: AnalysisSpec
    target_request: dict[str, Any]
    expected_discrimination: str = Field(min_length=1, max_length=1000)
    alternative_explanations: tuple[Annotated[str, Field(min_length=1, max_length=1000)], ...] = Field(min_length=1, max_length=10)
    limitations: tuple[str, ...] = (
        "A local declaration records ordering, not external preregistration or freedom from adaptive selection.",
        "Inference is conditional on declared association assumptions and compatible variable/endpoint meanings.",
        "Case-ID disjointness is observed within retained complete queries, not proof against hidden participant linkage, confounding or leakage.",
        "Replay or a replication ID alone never establishes independent biological corroboration.",
        "Replicated means recovery of the declared directional minimum effect, not equivalence to the original effect magnitude.",
    )

    @model_validator(mode="after")
    def compatible_contract(self):
        baseline, target = self.baseline_analysis, self.target_analysis
        if len(canonical_bytes(self.target_request))>32768:
            raise ValueError("follow-up source request exceeds declaration byte bound")
        if self.baseline_measurement.kind != "measurement" or self.baseline_input.kind != "acquisition":
            raise ValueError("follow-up requires exact baseline measurement/input references")
        if target.inputs or target.source_refs or not baseline.test_plan or not target.test_plan:
            raise ValueError("declare an unexecuted target contract with a retained hypothesis test")
        if baseline.method != target.method or baseline.estimand != target.estimand or baseline.fields != target.fields or baseline.entity_unit != target.entity_unit or baseline.entity_field != target.entity_field:
            raise ValueError("effect scales, fields, methods and entity contracts must be comparable")
        if self.kind == "independent_replication" and any(baseline.transformations.get(axis,"identity")!=target.transformations.get(axis,"identity") for axis in ("x","y")):
            raise ValueError("independent replication holds preprocessing fixed")
        left, right = baseline.test_plan, target.test_plan
        if (left.hypothesis_id, left.direction, left.minimum_effect) != (right.hypothesis_id, right.direction, right.minimum_effect):
            raise ValueError("follow-up cannot change the tested hypothesis, direction or effect threshold")
        if right.alpha > left.alpha or not set(left.multiplicity_family) <= set(right.multiplicity_family) or self.comparison_id not in right.multiplicity_family:
            raise ValueError("declare the comparison in a non-relaxed multiplicity family")
        if target.method not in {"pearson_correlation", "ordinary_least_squares"} or target.entity_unit not in {"case", "patient"} or target.entity_field != "id":
            raise ValueError("current follow-up supports only GDC case-keyed paired associations")
        return self


class FollowupResult(BaseModel, frozen=True):
    version: Literal["source-followup-v1"] = "source-followup-v1"
    followup_id: str
    block_id: str
    baseline_measurement: ExecutionReference
    target_measurement: ExecutionReference | None = None
    target_input: ExecutionReference
    stage: Literal["completed", "invalid", "operational_failed", "interrupted"]
    outcome: Literal["replicated", "not_replicated", "contradictory", "sensitivity_dependent", "consistent", "inconclusive", "attempted", "invalid"]
    independence: Literal["observed_disjoint_complete_case_queries", "overlap", "unknown"] = "unknown"
    confirmation_access: Literal["fresh_local_query", "previously_accessed", "unknown", "not_applicable"] = "unknown"
    overlap_count: int | None = Field(default=None, ge=0)
    intervals: dict[str, float] = Field(default_factory=dict)
    unresolved: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    @model_validator(mode="after")
    def outcome_contract(self):
        if self.target_input.kind!="acquisition" or self.target_input.block_id!=self.block_id or self.baseline_measurement.kind!="measurement":
            raise ValueError("follow-up result requires exact input and measurement lineage")
        if any(not math.isfinite(v) for v in self.intervals.values()):
            raise ValueError("undefined uncertainty cannot establish follow-up outcomes")
        if self.stage=="completed":
            if self.target_measurement is None or self.target_measurement.kind!="measurement" or self.target_measurement.block_id!=self.block_id or self.outcome in {"attempted","invalid"}:
                raise ValueError("completed comparison requires exact owned measurement")
            if self.outcome!="inconclusive" and set(self.intervals)!={"baseline_low","baseline_high","target_low","target_high"}:
                raise ValueError("qualified outcomes require original and target effect intervals")
            if self.outcome in {"replicated","not_replicated","contradictory"} and self.independence!="observed_disjoint_complete_case_queries":
                raise ValueError("replication outcomes require observed disjoint complete case queries")
            if self.outcome in {"replicated","not_replicated","contradictory"} and self.confirmation_access!="fresh_local_query":
                raise ValueError("replication outcomes require confirmation access after local declaration")
            if self.outcome in {"consistent","sensitivity_dependent"} and self.independence!="overlap":
                raise ValueError("sensitivity outcomes require observed case overlap")
        elif self.target_measurement is not None or self.outcome!=("invalid" if self.stage=="invalid" else "attempted"):
            raise ValueError("uncompleted comparisons cannot establish scientific outcomes")
        return self


def canonical_case_ids(record):
    if record.source != "gdc" or record.coverage is None or record.coverage.endpoint != "cases": return None
    result=set()
    for row in record.records:
        identity=row.get("id")
        if not isinstance(identity,str) or row.get("case_id")!=identity: return None
        try: canonical=str(UUID(identity))
        except ValueError: return None
        if canonical in result: return None
        result.add(canonical)
    return result


def case_overlap(left, right):
    first, second = canonical_case_ids(left), canonical_case_ids(right)
    if first is None or second is None: return "unknown", None
    overlap = len(first & second)
    if overlap: return "overlap", overlap
    if not first or not second or not left.coverage.complete or not right.coverage.complete:
        return "unknown", 0
    return "observed_disjoint_complete_case_queries", 0


def compare_followup(plan: FollowupPlan, baseline: MeasuredResult, target: MeasuredResult,
                     baseline_input: AcquisitionRecord, target_input: AcquisitionRecord, target_reference,
                     confirmation_access="unknown"):
    """Compare complete intervals against a frozen effect bound, never significance flags."""
    independence, overlap = case_overlap(baseline_input, target_input)
    result = FollowupResult(followup_id=plan.followup_id, block_id=plan.block_id,
        baseline_measurement=plan.baseline_measurement, target_measurement=target_reference,
        target_input=ExecutionReference(kind="acquisition", value=target_input.acquisition_id,
            block_id=plan.block_id, sha256=content_hash(target_input.model_dump(mode="json"))),
        stage="completed", outcome="inconclusive", independence=independence, overlap_count=overlap,
        confirmation_access=confirmation_access,
        limitations=(*plan.limitations, *baseline.limitations, *target.limitations))
    if baseline.origin != "source" or target.origin != "source":
        raise InvalidAnalysis("provided/synthetic inputs cannot establish source follow-up outcomes")
    original = baseline.diagnostics.get("hypothesis_test", {})
    check = target.diagnostics.get("hypothesis_test", {})
    if original.get("outcome") != "supported" or not check:
        return result.model_copy(update={"unresolved": ("Original effect-bound support or target uncertainty is unavailable.",)})
    intervals = {f"{name}_{bound}": measured.values[f"effect_ci_{bound}"]
                 for name, measured in (("baseline", baseline), ("target", target)) for bound in ("low", "high")}
    result = result.model_copy(update={"intervals": intervals})
    if plan.kind=="independent_replication" and confirmation_access!="fresh_local_query":
        return result.model_copy(update={"unresolved":("Confirmation values were previously accessed or local exposure history is unresolved; no held-out replication claim.",)})
    if plan.kind == "independent_replication" and independence != "observed_disjoint_complete_case_queries":
        return result.model_copy(update={"unresolved": ("Independent replication is unresolved: retained case IDs overlap or coverage/identity is unknown.",)})
    if plan.kind == "sensitivity" and independence != "overlap":
        return result.model_copy(update={"unresolved": ("Same-participant sensitivity requires observed retained case overlap.",)})
    low, high = intervals["target_low"], intervals["target_high"]
    protocol = plan.target_analysis.test_plan
    low, high = (low, high) if protocol.direction == "positive" else (-high, -low)
    bound = protocol.minimum_effect
    if low > bound:
        outcome = "replicated" if plan.kind == "independent_replication" else "consistent"
    elif high < -bound:
        outcome = "contradictory" if plan.kind == "independent_replication" else "sensitivity_dependent"
    elif -bound < low and high < bound:
        outcome = "not_replicated" if plan.kind == "independent_replication" else "sensitivity_dependent"
    else:
        outcome = "inconclusive"
    reason = ("Target uncertainty does not discriminate the predeclared meaningful-effect bounds; non-significance is not absence.",) if outcome == "inconclusive" else ()
    return result.model_copy(update={"outcome": outcome, "unresolved": reason,
        "limitations": (*result.limitations, "Not-replicated means the target interval lies strictly inside the declared negligible-effect bounds; no zero-effect or population-wide absence claim.")})
