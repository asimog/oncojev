"""The sole public path from deterministic measurement to ScientificEvidence."""

from src.evidence.models import ScientificEvidence
from src.science.models import MeasuredResult
import math


def admit_scientific_evidence(result: MeasuredResult) -> ScientificEvidence:
    if result.deterministic is not True:
        raise ValueError("only deterministic measurements may be admitted")
    if not result.provenance:
        raise ValueError("evidence admission requires provenance")
    if result.origin not in {"source", "sandbox"}:
        raise ValueError("evidence requires a source-bound or replay-validated measurement")
    if not result.source_refs:
        raise ValueError("evidence admission requires immutable source references")
    for value in result.values.values():
        if isinstance(value, (int, float)) and not isinstance(value, bool) and not math.isfinite(float(value)):
            raise ValueError("evidence values must be finite")
    return ScientificEvidence(measurement=result)
