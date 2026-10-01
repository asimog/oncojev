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
    version: str = "global-frontier-v1"
    objective: str
    basis: str
    candidates: tuple[Investigation, ...] = Field(max_length=20)
    beam: tuple[str, ...] = Field(max_length=5)
    omitted: int = Field(ge=0)
    relations: tuple[dict[str, Any], ...] = Field(max_length=40)
    limitations: tuple[str, ...] = (
        "Semantic relations and rejection are not scientific findings or resolutions.",
        "Application and verification-history revision pins await H5.",
        "Lexical retrieval can miss synonyms; labelled utility remains unverified.",
    )


MATERIAL_KINDS = (RecordKind.CYCLE, RecordKind.OUTCOME_CORRECTION, RecordKind.BLOCK,
                  RecordKind.STATE_REVISION, RecordKind.EVIDENCE, RecordKind.VERIFICATION,
                  RecordKind.BLOCK_DELTA, RecordKind.MEMORY_DIGEST)


def current_basis(runtime) -> str:
    store = runtime.repository.store
    # Global measurements/notes do not invalidate themselves. Scientific and
    # operational block changes do; no mutable in-memory counter is a basis.
    latest = {kind.value: record.seq if (record := store.latest(kind)) else 0 for kind in MATERIAL_KINDS}
    return content_hash({"records": latest, "index": runtime.oncolab.snapshot_id,
                         "mission": runtime.mission_id, "version": "global-frontier-v1"})


def generate(digests, *, limit=20):
    """Retain original references, preserve distinct tests/replication, dedup exact scope."""
    candidates = {}
    omitted = 0
    for digest in digests:
        for field in ("continuation_proposals", "uncertainties", "hypotheses", "operational_blockers", "candidates"):
            for item in getattr(digest, field):
                if not item.references or not item.summary.strip():
                    continue
                details = item.details
                scope = {key: (details[key] if isinstance(details.get(key), bool) else str(details[key])[:500] if details.get(key) is not None else None) for key in
                         ("proposed_test", "population", "design", "method", "replication", "capability_id")}
                scope.update(entities=digest.entities[:5], topics=digest.topics[:5])
                # An underspecified test or replication is not known to duplicate
                # another block. Never collapse two independent original records.
                origin = tuple(r.block_id or r.record_id for r in item.references)
                identity_scope = {key: normalize(value) if isinstance(value, str) else value for key, value in scope.items()}
                key = content_hash({"statement": normalize(item.summary), "scope": identity_scope,
                                    "origin": origin if not scope["proposed_test"] or scope["replication"] else None})
                if key in candidates:
                    old = candidates[key]
                    refs = tuple({r.seq: r for r in (*old.source_refs, *item.references)}.values())[:20]
                    candidates[key] = old.model_copy(update={"source_refs": refs})
                elif len(candidates) < limit:
                    candidates[key] = Investigation(candidate_id=key, objective=item.summary[:1000], origin=field,
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
