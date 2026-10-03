from pydantic import BaseModel,Field
from src.block.models import BlockStatus, RunOutcome, ObjectiveAttainment
from typing import Literal

class DossierStatement(BaseModel, frozen=True):
 statement_id:str
 statement:str
 epistemic_type:Literal["descriptive", "interpretation", "hypothesis", "uncertainty"]
 evidence_refs:tuple[str,...]=()
 unresolved_refs:tuple[str,...]=()
 semantic_status:Literal["measured","unavailable","not_requested"]="not_requested"
 semantic_call_id:str|None=None

class JevBlockDossier(BaseModel,frozen=True):
 lifecycle_status:BlockStatus=BlockStatus.INTERRUPTED
 run_outcome:RunOutcome=RunOutcome.NOT_STARTED
 objective_attainment:ObjectiveAttainment=ObjectiveAttainment.UNKNOWN
 operational_failures:tuple[dict,...]=()
 statements:tuple[DossierStatement,...]=()
 block_id:str; objective:str; termination_reason:str; evidence_refs:tuple[str,...]
 positive_findings:tuple[str,...]=(); hypotheses:tuple[str,...]=(); unresolved_uncertainties:tuple[str,...]=()
 important_jev_measurements:tuple[str,...]=(); frontier_decisions:tuple[str,...]=(); analyses_performed:tuple[str,...]=()
 resource_usage:dict[str,int]=Field(default_factory=dict); recommended_next_blocks:tuple[str,...]=()
 preferred_continuation:str; preferred_continuation_reason:str
