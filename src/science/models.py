from typing import Any, Literal
from pydantic import BaseModel,Field
class AnalysisSpec(BaseModel, frozen=True):
    analysis_id:str; question:str; population:str; estimand:str; method:str; variables:tuple[str,...]; inputs:dict[str,list[float]]=Field(default_factory=dict)
    source_refs:tuple[str,...]=()
    entity_field: str | None = None
    fields: dict[str,str] = Field(default_factory=dict)
    design: str = "descriptive response slice"
    entity_unit: str = "record"
    transformations: dict[str,Literal["identity","log1p"]] = Field(default_factory=dict)
    covariates: tuple[str,...] = ()
    missingness_policy: Literal["complete_pair"] = "complete_pair"
    replication_id: str | None = None
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
