from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator
from src.provenance import ExecutionReference
class InvalidAnalysis(ValueError):
    """A deterministic input/design rejection, separate from operational failure."""


class HypothesisTestPlan(BaseModel, frozen=True):
    """Exploratory directional association, conditional on declared model assumptions."""
    hypothesis_id: str = Field(min_length=1, max_length=200)
    direction: Literal["positive", "negative"]
    minimum_effect: float = Field(gt=0, allow_inf_nan=False)
    alpha: float = Field(default=0.05, gt=0, lt=0.2, allow_inf_nan=False)
    multiplicity_family: tuple[str, ...] = Field(min_length=1, max_length=1000)
    interpretation: Literal["exploratory_association"] = "exploratory_association"

    @model_validator(mode="after")
    def complete_family(self):
        if len(set(self.multiplicity_family)) != len(self.multiplicity_family) or self.hypothesis_id not in self.multiplicity_family:
            raise ValueError("declare a unique multiplicity family containing this hypothesis")
        return self


class AnalysisSpec(BaseModel, frozen=True):
    analysis_id:str; question:str; population:str; estimand:str; method:str; variables:tuple[str,...]; inputs:dict[str,list[float]]=Field(default_factory=dict)
    source_refs:tuple[str,...]=()
    entity_field: str | None = None
    fields: dict[str,str] = Field(default_factory=dict)
    design: str = "descriptive response slice"
    entity_unit: str = "record"
    transformations: dict[str,Literal["identity","log1p","zscore"]] = Field(default_factory=dict)
    covariates: tuple[str,...] = ()
    missingness_policy: Literal["complete_pair"] = "complete_pair"
    replication_id: str | None = None
    test_plan: HypothesisTestPlan | None = None
class MeasuredResult(BaseModel, frozen=True):
    analysis_id:str=Field(min_length=1)
    values:dict[str,Any]
    provenance:tuple[str,...]=Field(min_length=1)
    origin:Literal["source","sandbox","provided","synthetic"]="provided"
    source_refs:tuple[str,...]=()
    input_sha256:str=Field(min_length=64,max_length=64)
    limitations:tuple[str,...]=()
    deterministic:Literal[True]=True
    analysis_key: str | None = None
    replication_id: str | None = None
    interpretation: Literal["descriptive","associative","exploratory","unclassified"] = "unclassified"
    diagnostics: dict[str,Any] = Field(default_factory=dict)


class ScientificAttempt(BaseModel, frozen=True):
    version: Literal["scientific-attempt-v1"] = "scientific-attempt-v1"
    attempt_id: str
    block_id: str
    capability_id: str
    analysis: AnalysisSpec
    input_reference: ExecutionReference
    hypothesis_record_seq: int | None = Field(default=None, gt=0)
    stage: Literal["started", "completed", "invalid", "operational_failed", "interrupted"]
    outcome: Literal["attempted", "unknown", "invalid", "inconclusive", "supported", "contradicted"]
    measurement_reference: ExecutionReference | None = None
    failure_type: str | None = None
    limitations: tuple[str, ...] = (
        "Declared designs and exploratory tests are not preregistered confirmation.",
        "Execution failure, semantic rejection and non-significance are not scientific negatives.",
    )

    @model_validator(mode="after")
    def stage_contract(self):
        if self.input_reference.kind != "acquisition" or self.input_reference.block_id != self.block_id or self.analysis.inputs:
            raise ValueError("scientific attempt requires owned retained source inputs")
        if bool(self.hypothesis_record_seq) != bool(self.analysis.test_plan):
            raise ValueError("hypothesis test lineage is required exactly when a test is declared")
        if self.stage == "completed":
            ref = self.measurement_reference
            if ref is None or ref.kind != "measurement" or ref.block_id != self.block_id or ref.value != self.analysis.analysis_id:
                raise ValueError("completed attempt requires its exact owned measurement")
            if self.outcome in {"attempted", "invalid"}:
                raise ValueError("completed measurement cannot establish attempted/invalid outcome")
        else:
            expected = "invalid" if self.stage == "invalid" else "attempted"
            if self.measurement_reference is not None or self.outcome != expected:
                raise ValueError("attempt lifecycle cannot infer a scientific outcome")
        return self
