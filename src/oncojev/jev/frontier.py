from enum import StrEnum
from pydantic import BaseModel,Field
from oncojev.jev.models import ChoiceDecision,JevDecision,NoulDecision
class FrontierAction(StrEnum): ADVANCE="advance"; KEEP_ALIVE="keep_alive"; ESCALATE="escalate"; DEFER="defer"; REJECT_RETAIN="reject_retain"
class CandidateFrontierDecision(BaseModel,frozen=True): candidate_id:str; action:FrontierAction; provenance:tuple[str,...]=Field(min_length=1); rationale:str
class FrontierPolicy:
 def decide(self,candidate_id:str,decisions:tuple[JevDecision,...],provenance:tuple[str,...])->CandidateFrontierDecision:
  n=next((x for x in decisions if isinstance(x,NoulDecision)),None);c=next((x for x in decisions if isinstance(x,ChoiceDecision)),None)
  if n and .4<=n.p_true<=.6:return CandidateFrontierDecision(candidate_id=candidate_id,action=FrontierAction.KEEP_ALIVE,provenance=provenance,rationale="semantic uncertainty preserves recall")
  if c and abs(c.probabilities.get("ADVANCE",0)-c.probabilities.get("DEFER",0))<.2:return CandidateFrontierDecision(candidate_id=candidate_id,action=FrontierAction.KEEP_ALIVE,provenance=provenance,rationale="close choice distribution preserves beam")
  return CandidateFrontierDecision(candidate_id=candidate_id,action=FrontierAction.ADVANCE,provenance=provenance,rationale="live branch")
