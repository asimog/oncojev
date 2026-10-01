from pydantic import BaseModel,Field
from src.block.models import BlockStatus, RunOutcome, ObjectiveAttainment
class JevBlockDossier(BaseModel,frozen=True):
 lifecycle_status:BlockStatus=BlockStatus.INTERRUPTED
 run_outcome:RunOutcome=RunOutcome.NOT_STARTED
 objective_attainment:ObjectiveAttainment=ObjectiveAttainment.UNKNOWN
 operational_failures:tuple[dict,...]=()
 block_id:str; objective:str; termination_reason:str; evidence_refs:tuple[str,...]
 positive_findings:tuple[str,...]=(); hypotheses:tuple[str,...]=(); unresolved_uncertainties:tuple[str,...]=()
 important_jev_measurements:tuple[str,...]=(); frontier_decisions:tuple[str,...]=(); analyses_performed:tuple[str,...]=()
 resource_usage:dict[str,int]=Field(default_factory=dict); recommended_next_blocks:tuple[str,...]=()
 preferred_continuation:str; preferred_continuation_reason:str
Dossier=JevBlockDossier
