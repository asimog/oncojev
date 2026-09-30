from enum import StrEnum
from typing import Literal
from pydantic import BaseModel,Field
class JevQuestionSpec(BaseModel,frozen=True):
 question_id:str; semantic_purpose:str; primitive:Literal["noul","choice","score"]; projection_id:str; instructions:str; criteria:object; question_version:str; known_exclusions:tuple[str,...]=(); failure_semantics:str="failure is not judgment"; provenance:tuple[str,...]=(); status:Literal["local"]="local"
class NoulDecision(BaseModel,frozen=True): question_id:str; p_true:float=Field(ge=0,le=1); model_requested:str; model_resolved:str; question_version:str; projection_id:str
class ChoiceDecision(BaseModel,frozen=True): question_id:str; selected_option:str; probabilities:dict[str,float]; confidence:float=Field(ge=0,le=1); model_requested:str; model_resolved:str; question_version:str; projection_id:str
class ScoreDecision(BaseModel,frozen=True): question_id:str; expected_score:float; level_probabilities:dict[int,float]; confidence:float=Field(ge=0,le=1); model_requested:str; model_resolved:str; question_version:str; projection_id:str
JevDecision=NoulDecision|ChoiceDecision|ScoreDecision
class JevFailureCategory(StrEnum): TIMEOUT="timeout"; RATE_LIMIT="rate_limit"; TRANSPORT="transport"; VALIDATION="validation"; SERVICE="service"
class JevExecutionFailure(BaseModel,frozen=True): question_id:str; category:JevFailureCategory; detail:str
