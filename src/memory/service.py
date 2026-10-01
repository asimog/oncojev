"""Deterministic memory derivation and bounded retrieval over persisted records."""

import re
from datetime import datetime

from src.memory.models import CycleDigest, MemoryContext, MemoryItem, MemoryReference, StartMemory
from src.persistence.records import RecordKind, StoredRecord
from src.persistence.reconstruct import effective_cycle, reconstruct_block
from src.provenance import canonical_bytes, content_hash


def reference(record: StoredRecord) -> MemoryReference:
    return MemoryReference(kind=record.kind.value, record_id=record.record_id, seq=record.seq,
                           block_id=record.block_id, sha256=content_hash(record.payload))


def terms(text):
    return set(re.findall(r"[\w-]+", text.casefold()))


class ResearchMemory:
    max_results = 20

    def __init__(self, store):
        self.store = store

    def resolve(self, ref: MemoryReference):
        record = self.store.record_at(ref.seq)
        if record is None or record.kind.value != ref.kind or record.record_id != ref.record_id or record.block_id != ref.block_id or content_hash(record.payload) != ref.sha256:
            raise ValueError("unresolved or changed memory reference")
        return record.payload

    def validate(self, digest):
        for ref in digest.references:
            self.resolve(ref)
        for field in (digest.hypotheses, digest.scientific_negative_findings, digest.candidates,
                      digest.operational_blockers, digest.uncertainties, digest.continuation_proposals, digest.legacy_notes):
            for item in field:
                for ref in item.references:
                    self.resolve(ref)
        if digest.director_note is not None:
            for ref in digest.director_note.references:
                self.resolve(ref)

    def backfill(self):
        """Append derived snapshots; corrections invalidate snapshots, never overwrite them."""
        cycles = list(self.store.records(kind=RecordKind.CYCLE))
        covered = {b for c in cycles for b in c.payload.get("block_ids", ())}
        for block_id in self.store.block_ids():
            block = self.store.latest(RecordKind.BLOCK, block_id=block_id)
            if block and block_id not in covered and block.payload.get("status") in {"complete", "failed", "interrupted"}:
                cycles.append(block)
        saved = {r.record_id for r in self.store.records(kind=RecordKind.MEMORY_DIGEST)}
        for cycle in cycles:
            digest = self._derive(cycle)
            if digest.digest_id not in saved:
                self.validate(digest)
                self.store.append(StoredRecord(kind=RecordKind.MEMORY_DIGEST, record_id=digest.digest_id,
                                              payload=digest.model_dump(mode="json")))
                saved.add(digest.digest_id)
        linked_notes = {ref.seq for d in self.digests() for item in (*d.legacy_notes, *((d.director_note,) if d.director_note else ())) for ref in item.references}
        for note in self.store.records(kind=RecordKind.RESEARCH_MEMORY):
            if note.seq in linked_notes:
                continue
            digest = CycleDigest(digest_id=f"legacy:{note.seq}:{content_hash(note.payload)}", cycle_id=f"legacy:{note.seq}",
                mission_id=note.payload.get("mission_id"), direction="", recorded_at=note.recorded_at,
                cycle_status="unknown", director_outcome="unknown", inferred=True,
                limitations=("Unassociated legacy prose; no outcome, evidence or scientific result can be inferred.",),
                legacy_notes=(MemoryItem(item_id=note.record_id, summary=note.payload.get("summary", ""),
                    epistemic_status="legacy_prose", references=(reference(note),)),))
            if digest.digest_id not in saved:
                self.store.append(StoredRecord(kind=RecordKind.MEMORY_DIGEST, record_id=digest.digest_id, payload=digest.model_dump(mode="json")))

    def _derive(self, cycle):
        orphan = cycle.kind == RecordKind.BLOCK
        payload = {"block_ids": [cycle.block_id], "mission_id": cycle.payload.get("mission_id"),
                   "direction": cycle.payload["start"]["objective"], "status": "incomplete"} if orphan else effective_cycle(self.store, cycle.payload)
        block_ids = tuple(payload.get("block_ids", ()))
        records = [cycle]
        for block_id in block_ids:
            records.extend(r for r in self.store.records(block_id=block_id) if r.kind != RecordKind.MEMORY_DIGEST)
        notes = [r for r in self.store.records(kind=RecordKind.RESEARCH_MEMORY)
                 if r.payload.get("cycle_id") == cycle.record_id or
                 (not r.payload.get("cycle_id") and payload.get("mission_id") and
                  (r.payload.get("mission_id") == payload["mission_id"] or r.record_id.startswith(payload["mission_id"] + ":memory:"))
                  and (orphan or r.seq < cycle.seq))]
        records.extend(notes)
        records = list({r.seq: r for r in records}.values())
        refs = tuple(reference(r) for r in records if r.kind in {RecordKind.CYCLE, RecordKind.BLOCK, RecordKind.DOSSIER,
            RecordKind.MEASUREMENT, RecordKind.EVIDENCE, RecordKind.STATE_REVISION, RecordKind.OUTCOME_CORRECTION})
        priority = {"evidence": 0, "measurement": 1, "dossier": 2, "outcome_correction": 3, "cycle": 4, "block": 5, "state_revision": 6}
        refs = tuple(sorted(refs, key=lambda r: (priority[r.kind], -r.seq)))
        fingerprint = content_hash([(r.seq, content_hash(r.payload)) for r in sorted(records, key=lambda r: r.seq)])
        hypotheses, candidates, blockers, uncertainties, proposals = [], [], [], [], []
        objectives, lifecycle, limitations, unresolved = [], [], [], []
        usage = {}
        entities, topics = set(), set()
        inferred = orphan or bool(payload.get("outcome_inferred"))
        for block_id in block_ids:
            view = reconstruct_block(self.store, block_id)
            if view.block is None:
                unresolved.append(f"block:{block_id}")
                continue
            objectives.append(view.block["start"]["objective"])
            entities.update(view.block["start"].get("entities", ()))
            topics.update(view.block["start"].get("topics", ()))
            lifecycle.append({"block_id": block_id, "status": view.block["status"], "run_outcome": view.run_outcome.value,
                              "termination_reason": view.block.get("termination_reason"), "inferred": view.outcome_inferred})
            inferred |= view.outcome_inferred
            unresolved.extend(view.unresolved_source_refs)
            for record in (r for r in records if r.block_id == block_id):
                if record.kind == RecordKind.MEASUREMENT:
                    limitations.extend(record.payload.get("limitations", ()))
                    if record.payload.get("origin") in {"provided", "synthetic"}:
                        limitations.append(f"{record.record_id}: exploratory {record.payload['origin']} input; not admitted evidence.")
                if record.kind == RecordKind.STATE_REVISION and record == self.store.latest(RecordKind.STATE_REVISION, block_id=block_id):
                    for fragment in record.payload.get("uncertainties", ()):
                        uncertainties.append(MemoryItem(item_id=fragment["fragment_id"], summary=fragment["summary"],
                            epistemic_status="uncertainty", references=(reference(record),)))
                    # Only explicitly labelled entities/topics support exact filters.
                    for fragment in (*record.payload.get("candidates", ()), *record.payload.get("observations", ())):
                        entities.update(str(e) for e in fragment.get("details", {}).get("entities", ()))
                        topics.update(str(e) for e in fragment.get("details", {}).get("topics", ()))
                if record.kind != RecordKind.LEDGER_EVENT:
                    continue
                event = record.payload
                data = event["payload"]
                kind = event["event_type"]
                ref = (reference(record),)
                if kind == "ReasonerOutput":
                    for i, h in enumerate(data.get("hypotheses", ())):
                        hypotheses.append(MemoryItem(item_id=f"{record.record_id}:{i}", summary=h["statement"],
                            epistemic_status="hypothesis", references=ref, details=h))
                        if h.get("proposed_test"):
                            proposals.append(MemoryItem(item_id=f"{record.record_id}:test:{i}", summary=h["proposed_test"],
                                epistemic_status="proposal", references=ref))
                    if data.get("uncertainty"):
                        uncertainties.append(MemoryItem(item_id=record.record_id, summary=data["uncertainty"], epistemic_status="uncertainty", references=ref))
                if kind == "FrontierDecision":
                    candidates.append(MemoryItem(item_id=data.get("candidate_id", record.record_id),
                        summary=data.get("candidate_summary", data.get("candidate_id", "semantic candidate")),
                        epistemic_status="semantic_history", references=ref, details=data))
                if kind in {"CapabilityFailure", "ResearcherRunFailed", "DirectorRunFailed", "DirectorRunTruncated", "InterruptedBlockRecovered", "CycleFinalizationFailed"}:
                    blockers.append(MemoryItem(item_id=record.record_id, summary=f"{kind}: {data.get('capability_id', '')} {data.get('error_type', data.get('reason', 'unknown'))}".strip(),
                                              epistemic_status="operational_failure", references=ref, details=data))
                if kind == "ScopeEscalationRequested" and data.get("proposed_test"):
                    proposals.append(MemoryItem(item_id=record.record_id, summary=data["proposed_test"], epistemic_status="proposal", references=ref))
                if kind == "ModelUsage":
                    usage[block_id] = dict(data)
            if view.dossier:
                usage.setdefault(block_id, {})["recorded_resources"] = view.dossier.get("resource_usage", {})
                evidence = {r.record_id for r in records if r.kind == RecordKind.EVIDENCE and r.block_id == block_id}
                unresolved.extend(f"evidence:{e}" for e in view.dossier.get("evidence_refs", ()) if e not in evidence)
        if payload.get("error_type") and not blockers:
            blockers.append(MemoryItem(item_id=cycle.record_id, summary=payload["error_type"], epistemic_status="operational_failure", references=(reference(cycle),)))
        if inferred:
            limitations.append("Historical outcome is inferred or corrected; closure does not establish scientific success.")
        limitations.append("Scientific negatives are not inferred from semantic rejection, missing evidence or provider failure.")
        legacy = tuple(MemoryItem(item_id=r.record_id, summary=r.payload.get("summary", ""), epistemic_status="legacy_prose", references=(reference(r),)) for r in notes if not r.payload.get("cycle_id"))
        current_note = next((MemoryItem(item_id=r.record_id, summary=r.payload.get("summary", ""), epistemic_status="director_note", references=(reference(r),))
                             for r in reversed(notes) if r.payload.get("cycle_id") == cycle.record_id), None)
        return CycleDigest(digest_id=f"{cycle.record_id}:{fingerprint}", cycle_id=cycle.record_id, mission_id=payload.get("mission_id"),
            direction=payload.get("direction", ""), recorded_at=cycle.recorded_at, cycle_status=payload.get("status", "incomplete"),
            director_outcome=payload.get("director_outcome", "unknown"), failure_reason=payload.get("error_type"), block_ids=block_ids,
            objectives=tuple(objectives), lifecycle=tuple(lifecycle), references=refs, limitations=tuple(dict.fromkeys(limitations)),
            unresolved_references=tuple(sorted(set(unresolved))), hypotheses=tuple(hypotheses), candidates=tuple(candidates),
            operational_blockers=tuple(blockers), uncertainties=tuple(uncertainties), continuation_proposals=tuple(proposals),
            resource_usage=usage, entities=tuple(sorted(entities)), topics=tuple(sorted(topics)), inferred=inferred, legacy_notes=legacy, director_note=current_note)

    def digests(self):
        latest = {}
        for record in self.store.records(kind=RecordKind.MEMORY_DIGEST):
            digest = CycleDigest.model_validate(record.payload)
            latest[digest.cycle_id] = digest
        for digest in latest.values():
            self.validate(digest)
        return tuple(latest.values())

    def search(self, query="", *, mission_id=None, entity=None, topic=None, since: datetime | None = None,
               until: datetime | None = None, limit=10):
        if not 1 <= limit <= self.max_results:
            raise ValueError("memory search limit must be between 1 and 20")
        ranked = []
        for d in self.digests():
            if mission_id is not None and d.mission_id != mission_id or entity is not None and entity not in d.entities or topic is not None and topic not in d.topics:
                continue
            if since is not None and d.recorded_at < since or until is not None and d.recorded_at > until:
                continue
            # Legacy Director prose never supplies relevance or facts.
            text = " ".join((d.direction, *d.objectives, *d.entities, *d.topics,
                             *(i.summary for field in (d.hypotheses, d.candidates, d.uncertainties, d.continuation_proposals) for i in field)))
            score = len(terms(query) & terms(text))
            if query and score == 0:
                continue
            ranked.append((score, d))
        ranked.sort(key=lambda pair: (-pair[0], pair[1].cycle_id, pair[1].digest_id))
        return tuple(d for _, d in ranked[:limit])

    def context(self, query, *, limit=5, **filters):
        digests = self.search(query, limit=limit, **filters)
        views = []
        for digest in digests:
            view = digest.model_dump(mode="json")
            truncated = {"direction": len(view["direction"]) > 1000,
                         "objectives": sum(len(s) > 1000 for s in view["objectives"][:20])}
            view["direction"] = view["direction"][:1000]
            view["objectives"] = [s[:1000] for s in view["objectives"][:20]]
            view["legacy_notes"] = []  # available only through explicit reference lookup
            view["director_note"] = None  # optional prose is not canonical retrieved context
            view["legacy_note_count"] = len(digest.legacy_notes)
            view["director_note_available"] = digest.director_note is not None
            view["resource_usage"] = {b: {"recorded_resources": v.get("recorded_resources", {})} for b, v in list(digest.resource_usage.items())[:20]}
            omitted = {}
            for key in ("references", "hypotheses", "scientific_negative_findings", "candidates", "operational_blockers", "uncertainties", "continuation_proposals", "limitations", "unresolved_references", "entities", "topics", "lifecycle"):
                omitted[key] = max(0, len(view[key]) - 20)
                view[key] = view[key][:20]
                truncated[key] = sum(len(i if isinstance(i, str) else i.get("summary", "")) > 1000 for i in view[key])
                for index, item in enumerate(view[key]):
                    if isinstance(item, str):
                        view[key][index] = item[:1000]
                    elif "summary" in item:
                        item["summary"] = item["summary"][:1000]
                        item["details"] = {}  # exact native distributions stay reference-resolvable
                        item["references"] = item["references"][:2]
            view["omitted_items"] = omitted
            view["truncated_text"] = truncated
            # Preserve a compact representative of each category before dropping
            # whole digests, so a large history cannot hide its failure reason.
            while len(canonical_bytes(view)) > 12288:
                fields = [k for k in omitted if len(view[k]) > 1]
                if not fields:
                    break
                key = max(fields, key=lambda k: len(canonical_bytes(view[k])))
                view[key].pop()
                omitted[key] += 1
            views.append(view)
        context = MemoryContext(query=query[:1000], digests=tuple(views))
        while len(canonical_bytes(context.model_dump(mode="json"))) > context.max_bytes and context.digests:
            context = context.model_copy(update={"digests": context.digests[:-1], "omitted_digests": context.omitted_digests + 1})
        return context

    def start_context(self, objective, context=None):
        context = context or self.context(objective, limit=5).model_dump(mode="json")
        views = context["digests"]
        refs = tuple(MemoryReference.model_validate(r) for d in views for r in d["references"])
        refs = tuple({r.seq: r for r in refs}.values())[:20]
        for ref in refs:
            self.resolve(ref)
        start = StartMemory(digest_ids=tuple(d["digest_id"] for d in views), references=refs,
            prior_failures=tuple(i["summary"] for d in views for i in d["operational_blockers"])[:20],
            uncertainties=tuple(i["summary"] for d in views for i in d["uncertainties"])[:20],
            candidate_directions=tuple(i["summary"] for d in views for i in (*d["candidates"], *d["continuation_proposals"]))[:20],
            limitations=tuple(dict.fromkeys(s for d in views for s in d["limitations"]))[:20], omitted_digests=context["omitted_digests"])
        while len(canonical_bytes(start.model_dump(mode="json"))) > 16384:
            field = max(("prior_failures", "uncertainties", "candidate_directions", "limitations", "references"),
                        key=lambda f: len(canonical_bytes(getattr(start, f) if f != "references" else [r.model_dump(mode="json") for r in start.references])))
            start = start.model_copy(update={field: getattr(start, field)[:-1], "omitted_items": start.omitted_items + 1})
        return start

    def get_dossier(self, block_id):
        view = reconstruct_block(self.store, block_id)
        return view.dossier

    def get_evidence(self, evidence_id, block_id):
        record = next((r for r in self.store.records(kind=RecordKind.EVIDENCE, block_id=block_id) if r.record_id == evidence_id), None)
        return {"reference": reference(record).model_dump(mode="json"), "evidence": record.payload} if record else None

    def items(self, field, query="", **filters):
        return tuple({"digest_id": d.digest_id, **i.model_dump(mode="json")} for d in self.search(query, **filters) for i in getattr(d, field))[:20]
