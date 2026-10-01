from enum import StrEnum
from typing import Literal
from typing import Any
from datetime import datetime
from pydantic import BaseModel,Field,model_validator
class JevQuestionSpec(BaseModel,frozen=True):
 question_id:str; semantic_purpose:str; primitive:Literal["noul","choice","score"]; projection_id:str; instructions:str|dict[str,Any]|list[Any]; criteria:object; question_version:str; known_exclusions:tuple[str,...]=(); failure_semantics:str="failure is not judgment"; provenance:tuple[str,...]=(); status:Literal["local"]="local"
 @model_validator(mode="after")
 def criteria_match_primitive(self)->"JevQuestionSpec":
  if self.primitive=="noul" and (not isinstance(self.criteria,dict) or not set(self.criteria).issubset({"true","false"})):
   raise ValueError("Noul criteria may only describe true and false outcomes")
  if self.primitive=="choice" and (not isinstance(self.criteria,dict) or len(self.criteria)<2):
   raise ValueError("Choice criteria require at least two named alternatives")
  if self.primitive=="score" and (not isinstance(self.criteria,(list,tuple)) or len(self.criteria)<2):
   raise ValueError("Score criteria require at least two ordered levels")
  return self
class NoulDecision(BaseModel,frozen=True): question_id:str; p_true:float=Field(ge=0,le=1); model_requested:str; model_resolved:str; question_version:str; projection_id:str
class ChoiceDecision(BaseModel,frozen=True): question_id:str; selected_option:str; probabilities:dict[str,float]; confidence:float=Field(ge=0,le=1); model_requested:str; model_resolved:str; question_version:str; projection_id:str
class ScoreDecision(BaseModel,frozen=True): question_id:str; expected_score:float; level_probabilities:dict[int,float]; confidence:float=Field(ge=0,le=1); model_requested:str; model_resolved:str; question_version:str; projection_id:str
JevDecision=NoulDecision|ChoiceDecision|ScoreDecision
class JevFailureCategory(StrEnum): TIMEOUT="timeout"; RATE_LIMIT="rate_limit"; TRANSPORT="transport"; VALIDATION="validation"; SERVICE="service"
class JevExecutionFailure(BaseModel,frozen=True): question_id:str; category:JevFailureCategory; detail:str


class JevCallReceipt(BaseModel, frozen=True):
 call_id:str
 block_id:str|None
 mission_id:str|None=None
 cycle_id:str|None=None
 context_type:str="candidate"
 context_identity:str|None=None
 candidate_id:str
 candidate_summary:str
 started_at:datetime
 duration_ms:float=Field(ge=0)
 outcome:Literal["started","completed","failed"]
 model_requested:str
 models_resolved:tuple[str,...]=()
 projection:dict[str,Any]|None=None
 projection_sha256:str|None=None
 questions:tuple[JevQuestionSpec,...]=()
 question_hashes:tuple[str,...]=()
 decisions:tuple[JevDecision,...]=()
 failures:tuple[JevExecutionFailure,...]=()
 reported_metadata:dict[str,Any]|None=None
 policy_version:str="candidate-frontier-v1"
