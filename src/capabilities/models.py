from enum import StrEnum

from pydantic import BaseModel, Field


class CapabilityKind(StrEnum):
    SOURCE = "source"
    SCIENTIFIC_METHOD = "scientific_method"
    STATISTICAL_METHOD = "statistical_method"
    TRANSFORMATION = "transformation"
    SOFTWARE = "software"
    VISUALIZATION = "visualization"
    LITERATURE = "literature"
    JEV = "jev"


class CapabilityAvailability(StrEnum):
    KNOWN = "known"
    AVAILABLE = "available"
    INSTALLED = "installed"
    ACQUIRABLE = "acquirable"
    VALIDATED = "validated"
    REUSABLE = "reusable"
    UNAVAILABLE = "unavailable"
    FORBIDDEN = "forbidden"


class CapabilityValidationState(StrEnum):
    UNVALIDATED = "unvalidated"
    VALIDATED = "validated"
    REUSABLE = "reusable"


class CapabilityExecutionMode(StrEnum):
    METADATA_ONLY = "metadata_only"
    LOCAL_PYTHON = "local_python"
    REMOTE_API = "remote_api"
    WRAPPER = "wrapper"
    SANDBOX = "sandbox"
    SEMANTIC_MEASUREMENT = "semantic_measurement"


class CapabilityAccessPolicy(StrEnum):
    PUBLIC = "public"
    LOCAL_ONLY = "local_only"
    CREDENTIALS_REQUIRED = "credentials_required"
    REVIEW_REQUIRED = "review_required"
    FORBIDDEN = "forbidden"


class ResourceClass(StrEnum):
    TRIVIAL = "trivial"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class CapabilityDescriptor(BaseModel, frozen=True):
    """Planning metadata only; descriptor presence never grants execution authority."""

    capability_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    kind: CapabilityKind
    purpose: str = Field(min_length=1)
    tags: tuple[str, ...] = ()
    input_contract: str
    output_contract: str
    applicability: str
    limitations: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    missingness_semantics: str
    availability: CapabilityAvailability
    execution_mode: CapabilityExecutionMode
    access_policy: CapabilityAccessPolicy
    implementation_or_source: str
    version: str | None = None
    resource_class: ResourceClass = ResourceClass.SMALL
    validation_state: CapabilityValidationState = CapabilityValidationState.UNVALIDATED
    provenance: tuple[str, ...] = Field(min_length=1)


class CapabilityStatus(StrEnum):
    LOCAL = "local"
    CANDIDATE = "candidate"
    VALIDATED = "validated"
    REUSABLE = "reusable"


class ScientificCapability(BaseModel, frozen=True):
    capability_id: str
    name: str
    description: str
    scientific_purpose: str
    input_contract: str
    output_contract: str
    applicability: str
    missingness_semantics: str
    implementation_reference: str
    version: str
    provenance: tuple[str, ...]
    validation_state: CapabilityStatus = CapabilityStatus.LOCAL


class JevCapability(BaseModel, frozen=True):
    capability_id: str
    semantic_purpose: str
    primitive: str
    required_state: str
    projection: str
    instructions: str
    criteria: object
    known_exclusions: tuple[str, ...] = ()
    failure_semantics: str = "operational failure is not judgment"
    status: CapabilityStatus = CapabilityStatus.LOCAL
