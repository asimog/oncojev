from enum import StrEnum
from pydantic import BaseModel,Field
from src.jev.models import ChoiceDecision,JevDecision,NoulDecision,ScoreDecision
class FrontierAction(StrEnum): ADVANCE="advance"; KEEP_ALIVE="keep_alive"; ESCALATE="escalate"; DEFER="defer"; REJECT_RETAIN="reject_retain"
class CandidateFrontierDecision(BaseModel,frozen=True): candidate_id:str; action:FrontierAction; provenance:tuple[str,...]=Field(min_length=1); rationale:str
class FrontierPolicy:
 def decide(self,candidate_id:str,decisions:tuple[JevDecision,...],provenance:tuple[str,...])->CandidateFrontierDecision:
  n=next((x for x in decisions if isinstance(x,NoulDecision)),None);c=next((x for x in decisions if isinstance(x,ChoiceDecision)),None);s=next((x for x in decisions if isinstance(x,ScoreDecision)),None)
  if c:
   ranked=sorted(c.probabilities.items(),key=lambda item:item[1],reverse=True)
   margin=ranked[0][1]-ranked[1][1] if len(ranked)>1 else ranked[0][1]
   if margin<.2:return CandidateFrontierDecision(candidate_id=candidate_id,action=FrontierAction.KEEP_ALIVE,provenance=provenance,rationale="close choice distribution preserves recall")
   if c.selected_option=="NONE":return CandidateFrontierDecision(candidate_id=candidate_id,action=FrontierAction.REJECT_RETAIN,provenance=provenance,rationale="no-fit choice retained for audit")
   if c.selected_option=="DEFER":return CandidateFrontierDecision(candidate_id=candidate_id,action=FrontierAction.DEFER,provenance=provenance,rationale="semantic policy deferred the candidate")
  if n and .4<=n.p_true<=.6:return CandidateFrontierDecision(candidate_id=candidate_id,action=FrontierAction.KEEP_ALIVE,provenance=provenance,rationale="semantic uncertainty preserves recall")
  if n and n.p_true<.25:return CandidateFrontierDecision(candidate_id=candidate_id,action=FrontierAction.REJECT_RETAIN,provenance=provenance,rationale="low relevance retained for audit")
  if s and s.confidence<.5:return CandidateFrontierDecision(candidate_id=candidate_id,action=FrontierAction.KEEP_ALIVE,provenance=provenance,rationale="low score confidence preserves recall")
  return CandidateFrontierDecision(candidate_id=candidate_id,action=FrontierAction.ADVANCE,provenance=provenance,rationale="policy supports local advancement")
