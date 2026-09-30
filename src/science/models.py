from typing import Any, Literal
from pydantic import BaseModel,Field
class AnalysisSpec(BaseModel, frozen=True):
    analysis_id:str; question:str; population:str; estimand:str; method:str; variables:tuple[str,...]; inputs:dict[str,list[float]]=Field(default_factory=dict)
class MeasuredResult(BaseModel, frozen=True):
    analysis_id:str=Field(min_length=1); values:dict[str,Any]; provenance:tuple[str,...]=Field(min_length=1); deterministic:Literal[True]=True
