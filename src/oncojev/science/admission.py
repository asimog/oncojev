"""The sole public path from deterministic measurement to ScientificEvidence."""

from oncojev.evidence.models import ScientificEvidence
from oncojev.science.models import MeasuredResult


def admit_scientific_evidence(result: MeasuredResult) -> ScientificEvidence:
    if result.deterministic is not True:
        raise ValueError("only deterministic measurements may be admitted")
    if not result.provenance:
        raise ValueError("evidence admission requires provenance")
    return ScientificEvidence(measurement=result)
