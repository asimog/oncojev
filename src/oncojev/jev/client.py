from collections.abc import Sequence
from typing import Protocol
from typesafe_sdk import Choice,Noul,Score,TypeSafeClient
import httpx2
from oncojev.jev.models import ChoiceDecision,JevDecision,JevQuestionSpec,NoulDecision,ScoreDecision
class JevClient(Protocol):
 def evaluate(self,state:dict,questions:Sequence[JevQuestionSpec])->tuple[JevDecision,...]:...
class TypeSafeJevClient:
 def __init__(self,api_key:str|None,model:str,http2:bool=True,base_url:str|None=None)->None:
  self._client=TypeSafeClient(api_key=api_key,model=model,base_url=base_url,http_client=httpx2.Client(http2=True) if http2 else None);self._model=model
 def evaluate(self,state:dict,questions:Sequence[JevQuestionSpec])->tuple[JevDecision,...]:
  sdk={q.question_id:Noul(instructions=q.instructions,criteria=q.criteria) if q.primitive=="noul" else Choice(instructions=q.instructions,criteria=q.criteria) if q.primitive=="choice" else Score(instructions=q.instructions,criteria=q.criteria) for q in questions}; response=self._client.system_one(state,sdk);out=[]
  for q in questions:
   a=response.answers[q.question_id];c=dict(question_id=q.question_id,model_requested=self._model,model_resolved=response.model,question_version=q.question_version,projection_id=q.projection_id)
   out.append(NoulDecision(**c,p_true=a.noul) if q.primitive=="noul" else ChoiceDecision(**c,selected_option=a.choice,probabilities=a.probabilities,confidence=a.confidence) if q.primitive=="choice" else ScoreDecision(**c,expected_score=a.score,level_probabilities=a.probabilities,confidence=a.confidence))
  return tuple(out)
class DeterministicJevClient:
 def evaluate(self,state:dict,questions:Sequence[JevQuestionSpec])->tuple[JevDecision,...]:
  out=[]
  for q in questions:
   c=dict(question_id=q.question_id,model_requested="deterministic-fixture",model_resolved="deterministic-fixture",question_version=q.question_version,projection_id=q.projection_id)
   out.append(NoulDecision(**c,p_true=.72) if q.primitive=="noul" else ChoiceDecision(**c,selected_option="ADVANCE",probabilities={"ADVANCE":.56,"DEFER":.44},confidence=.56) if q.primitive=="choice" else ScoreDecision(**c,expected_score=2.7,level_probabilities={0:.05,1:.1,2:.2,3:.45,4:.2},confidence=.65))
  return tuple(out)
