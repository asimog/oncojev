"""Bounded, reference-linked global proposals; never scientific admission."""
import unicodedata
from typing import Any, Literal

from pydantic import BaseModel, Field

from src.memory.models import MemoryReference
from src.persistence.records import RecordKind
from src.provenance import content_hash


def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


class Investigation(BaseModel, frozen=True):
    candidate_id: str
    objective: str = Field(max_length=1000)
    origin: str
    source_refs: tuple[MemoryReference, ...] = Field(min_length=1, max_length=20)
    scope: dict[str, Any]
    status: Literal["pending", "advance", "keep_alive", "defer", "reject_retain"] = "pending"
    semantic_call_id: str | None = None
    failure_type: str | None = None


class PreparedFrontier(BaseModel, frozen=True):
    frontier_id: str
    version: str = "global-frontier-v2"
    mission_id: str | None = None
    objective: str
    basis: str
    candidates: tuple[Investigation, ...] = Field(max_length=20)
    beam: tuple[str, ...] = Field(max_length=5)
    omitted: int = Field(ge=0)
    relations: tuple[dict[str, Any], ...] = Field(max_length=40)
    limitations: tuple[str, ...] = (
        "Semantic relations and rejection are not scientific findings or resolutions.",
        "Lexical retrieval can miss synonyms; labelled utility remains unverified.",
    )


MATERIAL_KINDS = (RecordKind.MISSION, RecordKind.ACQUISITION, RecordKind.REPRESENTATION_PARSE, RecordKind.EXTERNAL_LOOKUP, RecordKind.CYCLE, RecordKind.OUTCOME_CORRECTION, RecordKind.BLOCK,
                  RecordKind.STATE_REVISION, RecordKind.EVIDENCE, RecordKind.VERIFICATION,
                  RecordKind.BLOCK_DELTA, RecordKind.MEMORY_DIGEST, RecordKind.SCIENTIFIC_ATTEMPT, RecordKind.LITERATURE_CONTEXT, RecordKind.FOLLOWUP_PLAN, RecordKind.FOLLOWUP_RESULT)


def current_basis(runtime) -> str:
    store = runtime.repository.store
    # Global measurements/notes do not invalidate themselves. Scientific and
    # operational block changes do; no mutable in-memory counter is a basis.
    latest = {kind.value: record.seq if (record := store.latest(kind)) else 0 for kind in MATERIAL_KINDS}
    index = runtime.index_for()
    pin = runtime.institution.pin().model_dump(mode="json") if runtime.institution else None
    return content_hash({"records": latest, "index": index.snapshot_id, "institution": pin,
                         "mission": runtime.mission_id, "version": "global-frontier-v2"})


def generate(digests, *, limit=20):
    """Retain original references, preserve distinct tests/replication, dedup exact scope."""
    candidates = {}
    omitted = 0
    for digest in digests:
        for field in ("continuation_proposals", "uncertainties", "hypotheses", "scientific_followups", "scientific_attempts", "literature_contexts", "operational_blockers", "candidates"):
            for item in getattr(digest, field):
                if not item.references or not item.summary.strip():
                    continue
                details = item.details
                objective=item.summary
                scope = {key: (details[key] if isinstance(details.get(key), bool) else str(details[key])[:500] if details.get(key) is not None else None) for key in
                         ("proposed_test", "population", "design", "method", "replication", "capability_id", "hypothesis_id", "status", "related_hypothesis_id")}
                scope.update(entities=digest.entities[:5], topics=digest.topics[:5])
                if field=="scientific_followups":
                    outcome=details.get("outcome","unknown")
                    question=details.get("question") or item.summary
                    actions={
                        "replicated":"Test alternative explanations for the retained association",
                        "not_replicated":"Determine whether population/design differences or alternative explanations account for the effect-bound disagreement",
                        "contradictory":"Discriminate the retained opposite-direction findings while preserving their original scopes",
                        "sensitivity_dependent":"Determine which sensitivity assumptions or representation changes limit the retained association",
                        "consistent":"Assess independent-replication prerequisites for the retained same-participant robustness finding",
                        "inconclusive":"Resolve the retained information, identity or design limitations before interpreting the follow-up",
                        "invalid":"Repair the retained input/design validity problem before retesting",
                        "attempted":"Resolve prerequisites for the declared unfinished follow-up",
                        "unknown":"Resolve missing source/interpretation references before revisiting the follow-up",
                    }
                    action=actions.get(outcome,actions["unknown"])
                    purposes={"replicated":"alternative_explanation","not_replicated":"scope_disagreement","contradictory":"contradiction_resolution",
                        "sensitivity_dependent":"sensitivity_resolution","consistent":"independent_replication",
                        "inconclusive":"information_or_prerequisite","invalid":"repair_design","attempted":"unfinished_prerequisite","unknown":"resolve_references"}
                    objective=f"{action}: {question}"[:1000]
                    scope.update(proposed_test=action,source_outcome=outcome,basis_identity=item.item_id,
                        continuation_purpose=purposes.get(outcome,"resolve_references"),
                        unresolved=tuple(str(v)[:500] for v in details.get("unresolved",())[:3]),
                        alternative_explanations=tuple(str(v)[:500] for v in details.get("alternative_explanations",())[:3]),
                        scope_role="Originating context; Researcher selects the future operation.")
                # An underspecified test or replication is not known to duplicate
                # another block. Never collapse two independent original records.
                origin = tuple(r.block_id or r.record_id for r in item.references)
                identity_scope = {key: normalize(value) if isinstance(value, str) else value for key, value in scope.items()}
                key = content_hash({"statement": normalize(objective), "scope": identity_scope,
                                    "origin": origin if not scope["proposed_test"] or scope["replication"] else None})
                if key in candidates:
                    old = candidates[key]
                    refs = tuple({r.seq: r for r in (*old.source_refs, *item.references)}.values())[:20]
                    candidates[key] = old.model_copy(update={"source_refs": refs})
                elif len(candidates) < limit:
                    candidates[key] = Investigation(candidate_id=key, objective=objective[:1000], origin=field,
                                                    source_refs=item.references[:20], scope=scope)
                else:
                    omitted += 1
    return tuple(candidates.values()), omitted


class GlobalFrontierPolicy:
    version = "global-frontier-policy-v1"

    def interpret(self, candidate_id, decisions, questions, provenance, *, eligible=True, escalate=False):
        from src.jev.frontier import CandidateFrontierDecision, FrontierAction
        values = {q.semantic_purpose.split(".")[-1]: d.p_true
                  for q in questions for d in decisions if d.question_id == q.question_id and hasattr(d, "p_true")}
        if not eligible:
            action, reason = FrontierAction.DEFER, "deterministic prerequisite unavailable"
        elif not values or any(.25 <= p <= .75 for p in values.values()):
            action, reason = FrontierAction.KEEP_ALIVE, "unknown dimensions retain alternatives"
        elif values.get("mission_relevance", 1) < .25:
            action, reason = FrontierAction.REJECT_RETAIN, "low mission fit retained; not a scientific negative"
        elif values.get("dependency_readiness", 1) < .25 or values.get("capability_availability", 1) < .25:
            action, reason = FrontierAction.DEFER, "semantic prerequisite concern; no execution grant"
        else:
            action, reason = FrontierAction.ADVANCE, "separate compatible dimensions; Director chooses"
        return CandidateFrontierDecision(candidate_id=candidate_id, action=action, provenance=provenance, rationale=reason)


def beam(candidates):
    # Small categorical beam, no weighted scalar, duplicate penalty or mission stop.
    rank = {"advance": 0, "keep_alive": 1, "pending": 1, "defer": 2, "reject_retain": 3}
    allowed = [c for c in candidates if c.status not in {"defer", "reject_retain"}]
    return tuple(c.candidate_id for c in sorted(allowed, key=lambda c: rank[c.status])[:5])


class DirectorProposal(BaseModel, frozen=True):
    """Bounded authored question; grounding context is separate from result support."""
    objective: str = Field(min_length=1, max_length=1000)
    proposed_test: str = Field(min_length=1, max_length=500)
    population: str = Field(min_length=1, max_length=500)
    design: str = Field(min_length=1, max_length=500)
    capability_ids: tuple[str, ...] = Field(min_length=1, max_length=5)
    context_refs: tuple[MemoryReference, ...] = Field(min_length=1, max_length=10)
    prerequisite_refs: tuple[MemoryReference, ...] = Field(default=(), max_length=10)
    replication: str | None = Field(default=None, max_length=500)


def authored_investigations(runtime, proposals):
    from src.memory.service import reference
    if len(proposals) > 5:
        raise ValueError('at most five Director proposals per frontier')
    memory = runtime.memory_service()
    mission = next((r for r in reversed(runtime.repository.store.records(kind=RecordKind.MISSION))
                    if r.record_id == runtime.mission_id), None)
    if proposals and mission is None:
        raise ValueError('Director proposals require a retained current mission')
    candidates = []
    allowed = {RecordKind.INDEX_RECEIPT, RecordKind.EXTERNAL_LOOKUP, RecordKind.ACQUISITION,
               RecordKind.SCIENTIFIC_ARTIFACT, RecordKind.REPRESENTATION_PARSE, RecordKind.METHOD_CANDIDATES,
               RecordKind.INSTITUTIONAL_OBSERVATION, RecordKind.REGISTRY_REVISION, RecordKind.GLOBAL_RELATION,
               RecordKind.SCIENTIFIC_ATTEMPT, RecordKind.FOLLOWUP_RESULT, RecordKind.EVIDENCE}
    for proposal in proposals:
        proposal = DirectorProposal.model_validate(proposal)
        if not proposal.objective.strip() or any(ref.kind not in allowed for ref in proposal.context_refs):
            raise ValueError('inspected capability/source/relation context required')
        for ref in (*proposal.context_refs, *proposal.prerequisite_refs):
            memory.resolve(ref)
        if any(runtime.index_for().describe(identity) is None for identity in proposal.capability_ids):
            raise ValueError('unknown proposed capability')
        scope = {'proposed_test': proposal.proposed_test, 'population': proposal.population,
                 'design': proposal.design, 'replication': proposal.replication, 'capability_ids': proposal.capability_ids,
                 'mission_ref': reference(mission).model_dump(mode='json'),
                 'prerequisite_refs': [ref.model_dump(mode='json') for ref in proposal.prerequisite_refs],
                 'grounding_role': 'authored proposal context; scientific resolution remains unmeasured'}
        identity = content_hash({'mission': runtime.mission_id, 'objective': normalize(proposal.objective),
            'test': normalize(proposal.proposed_test), 'population': normalize(proposal.population),
            'design': normalize(proposal.design), 'replication': proposal.replication})
        candidates.append(Investigation(candidate_id=identity, objective=proposal.objective,
            origin='director_authored', source_refs=(reference(mission), *proposal.context_refs), scope=scope))
    return tuple(candidates)
