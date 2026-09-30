from enum import StrEnum
from pydantic import BaseModel
class CapabilityStatus(StrEnum): LOCAL="local"; CANDIDATE="candidate"; VALIDATED="validated"; REUSABLE="reusable"
class ScientificCapability(BaseModel,frozen=True):
 capability_id:str; name:str; description:str; scientific_purpose:str; input_contract:str; output_contract:str; applicability:str; missingness_semantics:str; implementation_reference:str; version:str; provenance:tuple[str,...]; validation_state:CapabilityStatus=CapabilityStatus.LOCAL
class JevCapability(BaseModel,frozen=True):
 capability_id:str; semantic_purpose:str; primitive:str; required_state:str; projection:str; instructions:str; criteria:object; known_exclusions:tuple[str,...]=(); failure_semantics:str="operational failure is not judgment"; status:CapabilityStatus=CapabilityStatus.LOCAL
