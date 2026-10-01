"""Declared application routes, not library-wide execution promises.

Facts about input ownership/presence are checked before semantic suitability.
These contracts mirror the small typed runtime tool surface.
"""
from pydantic import BaseModel, Field
from src.oncolab.models import OncoLabAccessPolicy, OncoLabExecutionMode


class ExecutionRoute(BaseModel, frozen=True):
    tool: str
    operation: str | None = None
    required_inputs: tuple[str, ...] = ()
    minimum_rows: int = Field(default=0, ge=0)
    exploratory: bool = False


ROUTES = {
    "science.acquisition-summary": (ExecutionRoute(tool="measure_acquisition", required_inputs=("acquisition",)),),
    "stat.scipy": (
        ExecutionRoute(tool="run_statistics", operation="pearson_correlation", required_inputs=("x", "y"), minimum_rows=2, exploratory=True),
        ExecutionRoute(tool="run_statistics", operation="independent_t_test", required_inputs=("group_a", "group_b"), minimum_rows=2, exploratory=True),
    ),
    "stat.pandas": (ExecutionRoute(tool="run_statistics", operation="descriptive_summary", required_inputs=("values",), minimum_rows=2, exploratory=True),),
    "stat.statsmodels": (ExecutionRoute(tool="run_statistics", operation="ordinary_least_squares", required_inputs=("x", "y"), minimum_rows=3, exploratory=True),),
    "source.gdc": (ExecutionRoute(tool="acquire_gdc"),),
    "source.ucsc-xena": (ExecutionRoute(tool="search_xena"),),
    "literature.public": (ExecutionRoute(tool="search_public_literature"),),
    "visualization.scientific": (ExecutionRoute(tool="create_line_figure", required_inputs=("x", "y"), exploratory=True),),
    "software.github-scientific": (ExecutionRoute(tool="acquire_github_scientific_method", required_inputs=("sandbox",)),),
}


def check_routes(descriptor, available_inputs: dict[str, int | bool], operation: str | None = None):
    """Missing prerequisites remain explicit; availability flags cannot grant a route."""
    reasons = []
    if descriptor.execution_mode == OncoLabExecutionMode.METADATA_ONLY:
        reasons.append("metadata_only")
    if descriptor.access_policy not in {OncoLabAccessPolicy.PUBLIC, OncoLabAccessPolicy.LOCAL_ONLY}:
        reasons.append("access_not_approved")
    if descriptor.availability.value in {"unavailable", "forbidden", "known"}:
        reasons.append("declared_unavailable")
    routes = tuple(r for r in ROUTES.get(descriptor.capability_id, ()) if operation is None or r.operation == operation)
    if not routes:
        reasons.append("no_declared_application_route")
    results = []
    for route in routes:
        missing = [k for k in route.required_inputs if not available_inputs.get(k)]
        undersized = [k for k in route.required_inputs if isinstance(available_inputs.get(k), int)
                      and not isinstance(available_inputs.get(k), bool) and available_inputs[k] < route.minimum_rows]
        results.append({"route": route.model_dump(mode="json"), "eligible": not reasons and not missing and not undersized,
                        "reasons": [*reasons, *(f"missing_input:{k}" for k in missing), *(f"insufficient_rows:{k}" for k in undersized)]})
    return {"capability_id": descriptor.capability_id, "eligible": any(r["eligible"] for r in results),
            "reasons": reasons, "routes": results}
