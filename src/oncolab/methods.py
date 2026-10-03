"""Need-bound method alternatives; discovery never grants scientific authority."""
import math
from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.oncolab.execution import check_routes
from src.provenance import canonical_bytes, content_hash
from src.sources.representation import RepresentationNeed, assess_retained_representation, field_value


class ScientificNeed(BaseModel, frozen=True):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=1000)
    estimand: str = Field(min_length=1, max_length=1000)
    population: str = Field(min_length=1, max_length=1000)
    design: str = Field(min_length=1, max_length=1000)
    representation_need: RepresentationNeed

    @model_validator(mode="after")
    def bounded_consistent_need(self):
        if self.estimand != self.representation_need.estimand:
            raise ValueError("method and representation must share the declared estimand")
        if len(canonical_bytes(self.model_dump(mode="json"))) > 8192:
            raise ValueError("scientific need exceeds byte bound")
        return self


def method_inputs(records, need):
    """Check each owned representation independently; never join partial inputs."""
    assessments = []
    for record in records:
        checks = assess_retained_representation(record, need.representation_need)
        # Application numerical routes require actual finite values even when
        # the caller omitted a numeric_roles declaration.
        fields = need.representation_need.fields
        numerical = set(fields) & {"x", "y", "group_a", "group_b", "values"}
        rows = 0
        for row in record.records[:100]:
            values = {role: field_value(row, path) for role, path in fields.items()}
            if values and all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
                if role in numerical else value is not None for role, value in values.items()):
                rows += 1
        inputs = {"acquisition": True}
        if checks["eligible"]:
            inputs.update({role: rows for role in need.representation_need.fields})
        assessments.append({"acquisition_id": record.acquisition_id,
            "content_sha256": record.content_sha256, "checks": checks, "available_inputs": inputs})
    return assessments


def method_route_checks(index, capability_id, representations, operation=None):
    descriptor = index.describe(capability_id)
    results = []
    for representation in representations:
        checks = check_routes(descriptor, representation["available_inputs"], operation, routes=index.routes)
        checks.update(acquisition_id=representation["acquisition_id"], content_sha256=representation["content_sha256"])
        if not representation["checks"]["eligible"]:
            checks["eligible"] = False
            checks["reasons"].append("representation_prerequisites_unmet")
            for route in checks["routes"]:
                route["eligible"] = False
                route["reasons"].append("representation_prerequisites_unmet")
        results.append(checks)
    return results or [check_routes(descriptor, {}, operation, routes=index.routes)]


def method_alternative(index, capability_id, need, representations):
    descriptor = index.describe(capability_id)
    contract = index.describe_with_verification(capability_id)
    route_checks = method_route_checks(index, capability_id, representations)
    representation_ready = any(r["checks"]["eligible"] for r in representations)
    input_ready = representation_ready and any(checks["eligible"] for checks in route_checks)
    return {"candidate_id": content_hash({"need": need.model_dump(mode="json"),
                "contract": contract["contract_sha256"], "inputs": [(r["acquisition_id"], r["content_sha256"]) for r in representations]}),
        "capability_id": capability_id, "kind": descriptor.kind.value,
        "contract_sha256": contract["contract_sha256"],
        "declared_assumptions": list(descriptor.assumptions), "declared_limitations": list(descriptor.limitations),
        "input_contract": descriptor.input_contract, "output_contract": descriptor.output_contract,
        "implementation_or_source": descriptor.implementation_or_source,
        "route_checks": route_checks, "representation_ready": representation_ready,
        "input_ready": input_ready, "scientific_suitability": "unmeasured",
        "status": "available_for_assessment" if input_ready else "prerequisites_unmet",
        "limitations": ["Need/design/population declarations and source fields do not validate scientific applicability.",
            "Route availability, installed packages and metadata are separate from validated operations.",
            "Competing methods and unmet prerequisites remain alternatives; no execution or evidence admission occurs."]}
