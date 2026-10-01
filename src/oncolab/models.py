from enum import StrEnum

from pydantic import BaseModel, Field


class OncoLabKind(StrEnum):
    SOURCE = "source"
    SCIENTIFIC_METHOD = "scientific_method"
    STATISTICAL_METHOD = "statistical_method"
    TRANSFORMATION = "transformation"
    SOFTWARE = "software"
    VISUALIZATION = "visualization"
    LITERATURE = "literature"
    JEV = "jev"


class OncoLabAvailability(StrEnum):
    KNOWN = "known"
    AVAILABLE = "available"
    INSTALLED = "installed"
    ACQUIRABLE = "acquirable"
    VALIDATED = "validated"
    REUSABLE = "reusable"
    UNAVAILABLE = "unavailable"
    FORBIDDEN = "forbidden"


class OncoLabValidationState(StrEnum):
    UNVALIDATED = "unvalidated"
    VALIDATED = "validated"
    REUSABLE = "reusable"


class OncoLabExecutionMode(StrEnum):
    METADATA_ONLY = "metadata_only"
    LOCAL_PYTHON = "local_python"
    REMOTE_API = "remote_api"
    WRAPPER = "wrapper"
    SANDBOX = "sandbox"
    SEMANTIC_MEASUREMENT = "semantic_measurement"


class OncoLabAccessPolicy(StrEnum):
    PUBLIC = "public"
    LOCAL_ONLY = "local_only"
    CREDENTIALS_REQUIRED = "credentials_required"
    REVIEW_REQUIRED = "review_required"
    FORBIDDEN = "forbidden"


class OncoLabResourceClass(StrEnum):
    TRIVIAL = "trivial"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class OncoLabDescriptor(BaseModel, frozen=True):
    """Planning metadata only; descriptor presence never grants execution authority."""

    capability_id: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1)
    kind: OncoLabKind
    purpose: str = Field(min_length=1)
    tags: tuple[str, ...] = ()
    input_contract: str
    output_contract: str
    applicability: str
    limitations: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    missingness_semantics: str
    availability: OncoLabAvailability
    execution_mode: OncoLabExecutionMode
    access_policy: OncoLabAccessPolicy
    implementation_or_source: str
    version: str | None = None
    resource_class: OncoLabResourceClass = OncoLabResourceClass.SMALL
    validation_state: OncoLabValidationState = OncoLabValidationState.UNVALIDATED
    provenance: tuple[str, ...] = Field(min_length=1)


class OncoLabCapabilityStatus(StrEnum):
    LOCAL = "local"
    CANDIDATE = "candidate"
    VALIDATED = "validated"
    REUSABLE = "reusable"


class OncoLabCard(BaseModel, frozen=True):
    """Discovery only. Expand the ID before execution selection."""
    capability_id: str
    name: str
    kind: OncoLabKind
    purpose: str
    tags: tuple[str, ...]
    applicability: str
    input_summary: str
    limitations: tuple[str, ...]
    availability: OncoLabAvailability
    execution_mode: OncoLabExecutionMode
    access_policy: OncoLabAccessPolicy
    contract_sha256: str
    truncated: bool = False


class OncoLabPage(BaseModel, frozen=True):
    cards: tuple[OncoLabCard, ...]
    snapshot_id: str
    retrieval_version: str = "oncolab-retrieval-v2"
    continuation: str | None = None
    exhausted: bool
    total_candidates: int


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
    validation_state: OncoLabCapabilityStatus = OncoLabCapabilityStatus.LOCAL


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
    status: OncoLabCapabilityStatus = OncoLabCapabilityStatus.LOCAL
