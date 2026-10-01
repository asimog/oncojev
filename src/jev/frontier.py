from enum import StrEnum
from pydantic import BaseModel,Field
from src.jev.models import ChoiceDecision,JevDecision,NoulDecision,ScoreDecision
class FrontierAction(StrEnum): ADVANCE="advance"; KEEP_ALIVE="keep_alive"; ESCALATE="escalate"; DEFER="defer"; REJECT_RETAIN="reject_retain"
class CandidateFrontierDecision(BaseModel,frozen=True): candidate_id:str; action:FrontierAction; provenance:tuple[str,...]=Field(min_length=1); rationale:str
class FrontierPolicy:
 version = "semantic-frontier-v2"
 def interpret(self,candidate_id,decisions,questions,provenance,*,eligible=True,escalate=False):
  """Keep dimensions separate; conflicts/uncertainty preserve alternatives."""
  if not eligible:action,rationale=FrontierAction.DEFER,"deterministic prerequisite unavailable; semantic relevance cannot grant execution"
  elif not decisions:action,rationale=FrontierAction.KEEP_ALIVE,"no semantic measurement available; deterministic fallback"
  else:
   properties={q.question_id:q.semantic_purpose for q in questions}
   fit=[d.p_true for d in decisions if isinstance(d,NoulDecision) and properties.get(d.question_id,"").split(".")[-1] not in {"duplication","contradiction","capability_gap","actionability","overstatement"}]
   uncertain=any(.25<=p<=.75 for p in fit)
   conflicting=bool(fit and min(fit)<.25 and max(fit)>.75)
   if escalate and (uncertain or conflicting):action,rationale=FrontierAction.ESCALATE,"bounded review proposal; deadlines and scope unchanged"
   elif uncertain or conflicting:action,rationale=FrontierAction.KEEP_ALIVE,"ambiguous or conflicting dimensions; alternatives preserved"
   elif fit and min(fit)<.25:action,rationale=FrontierAction.REJECT_RETAIN,"explicit low fit retained; not a scientific negative"
   else:action,rationale=FrontierAction.ADVANCE,"compatible semantic context; Researcher chooses action"
  return CandidateFrontierDecision(candidate_id=candidate_id,action=action,provenance=provenance,rationale=rationale)
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
