from pydantic import BaseModel,Field
class Hypothesis(BaseModel,frozen=True): hypothesis_id:str; statement:str; within_scope:bool; proposed_test:str
class ReasonerOutput(BaseModel,frozen=True): interpretation:str; hypotheses:tuple[Hypothesis,...]=Field(min_length=1); uncertainty:str
