"""Qualified derived context; literature and semantic agreement never admit evidence."""
import math
from typing import Literal, get_args
from pydantic import BaseModel, Field
from src.memory.models import MemoryReference
from src.jev.frontier import CandidateFrontierDecision, FrontierAction


ContextCategory = Literal["known_result", "rediscovery", "known_mechanism_new_context",
                          "contradictory_finding", "potentially_novel_observation", "unknown"]


class LiteratureContext(BaseModel, frozen=True):
    version: Literal["literature-context-v1"] = "literature-context-v1"
    assessment_id: str
    block_id: str
    claim: str = Field(min_length=1, max_length=1000)
    category: ContextCategory = "unknown"
    epistemic_status: Literal["tentative_literature_context"] = "tentative_literature_context"
    basis: tuple[MemoryReference, ...] = Field(min_length=2)
    semantic_call_id: str | None = None
    semantic_status: Literal["measured", "insufficient_material", "unavailable"]
    unresolved: tuple[str, ...] = ()
    limitations: tuple[str, ...] = (
        "Classification is bounded to retained source material and declared analysis scope.",
        "Literature metadata/abstracts are not full text or independent scientific validation.",
        "Potential novelty is tentative search context, not proof of novelty, causality or clinical utility.",
        "Context agreement never changes measurements, admission or replication status.",
        "A declared replication ID or repeated computation does not establish independent replication.",
        "Native distribution thresholds are an uncalibrated annotation policy, not scientific confidence.",
    )


class LiteratureContextPolicy:
    version = "literature-context-v1"

    def interpret(self, candidate_id, decisions, questions, provenance, **kwargs):
        return CandidateFrontierDecision(candidate_id=candidate_id, action=FrontierAction.KEEP_ALIVE,
            provenance=provenance, rationale="Tentative context annotation only; no execution, rejection or admission authority.")


def category_from_native(decisions):
    """Keep native categorical and independent scope dimensions separate."""
    choice = next((d for d in decisions if d.get("question_id", "").endswith(":category")), None)
    scope = {d["question_id"].rsplit(":", 1)[-1]: d.get("p_true") for d in decisions
             if d.get("question_id", "").endswith((":claim_within_measurement", ":scope_known"))}
    if choice is None or any(not isinstance(scope.get(k), (int, float)) or not math.isfinite(scope[k]) or scope[k] <= .75
                             for k in ("claim_within_measurement", "scope_known")):
        return "unknown", "Claim support or required population/assay/endpoint scope remains unresolved."
    probabilities = choice.get("probabilities", {})
    if set(probabilities) != set(get_args(ContextCategory)) or any(not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p <= 1
                                for p in probabilities.values()) or abs(sum(probabilities.values()) - 1) > .01:
        return "unknown", "Native categorical distribution is unavailable or invalid."
    ranked = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
    selected = choice.get("selected_option")
    if selected != ranked[0][0] or ranked[0][1] <= .75 or len(ranked) < 2 or ranked[0][1] - ranked[1][1] < .25:
        return "unknown", "Native categorical alternatives are unresolved under the annotation policy."
    if selected == "unknown":
        return "unknown", "Native category remains unknown on the supplied material."
    return selected, ""  # Typed construction also checks the category vocabulary.
