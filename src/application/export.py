"""Deterministic public projections of pinned authoritative records."""
import hashlib
import json
from pathlib import Path
import re

from src.persistence.records import RecordKind
from src.provenance import content_hash


RENDERER = "oncojevlab-v2"
GROUPS = {
    "program": (RecordKind.MISSION, RecordKind.CYCLE, RecordKind.CYCLE_START, RecordKind.OUTCOME_CORRECTION),
    "program/reviews": (RecordKind.RESEARCH_MEMORY,),
    "program/frontier": (RecordKind.GLOBAL_FRONTIER,),
    "program/relations": (RecordKind.GLOBAL_RELATION,),
    "research/history": (RecordKind.MEMORY_DIGEST,),
    "capabilities/revisions": (RecordKind.REGISTRY_REVISION, RecordKind.REGISTRY_REVIEW),
    "capabilities/history": (RecordKind.INSTITUTIONAL_OBSERVATION,),
    "capabilities/proposals": (RecordKind.CAPABILITY_PROPOSAL,),
    "engineering/proposals": (RecordKind.ENGINEERING_PROPOSAL,),
    "verification": (RecordKind.VERIFICATION, RecordKind.REFERENCE_VALIDATION,
                     RecordKind.ENVIRONMENT_QUALIFICATION, RecordKind.DEPLOYMENT_VERIFICATION),
}
BLOCK_KINDS = (RecordKind.BLOCK, RecordKind.BLOCK_DELTA, RecordKind.DOSSIER,
               RecordKind.MEASUREMENT, RecordKind.EVIDENCE, RecordKind.SCIENTIFIC_ATTEMPT, RecordKind.LITERATURE, RecordKind.LITERATURE_CONTEXT, RecordKind.JEV_CALL)
PRIVATE = re.compile(r"(?:credential|secret|authorization|api_key|token|password|headers|content_base64|raw_json|messages|prompt|environment|experiment_path)", re.I)
TOKEN = re.compile(r"(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{16,}|Bearer\s+[^\s\"']+)")


def public_value(value):
    if isinstance(value, dict):
        return {k: public_value(v) for k, v in sorted(value.items()) if not PRIVATE.search(k)}
    if isinstance(value, (list, tuple)):
        return [public_value(v) for v in value]
    if isinstance(value, str):
        return TOKEN.sub("[redacted credential]", value)
    return value


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def _record(record):
    return {"kind": record.kind.value, "record_id": record.record_id, "seq": record.seq,
            "block_id": record.block_id, "recorded_at": record.recorded_at.isoformat(),
            "source_sha256": content_hash(record.payload), "payload": public_value(record.payload)}


def render_snapshot(store, *, high_water=None):
    """Read one immutable prefix. Rendering writes neither DB nor notebook state."""
    with store.transaction():
        ceiling = store.high_water() if high_water is None else high_water
        kinds = set(BLOCK_KINDS).union(*(set(kinds) for kinds in GROUPS.values()))
        selected = tuple(sorted((r for kind in kinds for r in store.records(kind=kind) if r.seq <= ceiling), key=lambda r: r.seq))
    files = {}
    for path, kinds in GROUPS.items():
        values = [_record(r) for r in selected if r.kind in kinds]
        if values:
            files[path + ".json"] = json_bytes(values)
    block_ids = sorted({r.block_id for r in selected if r.kind in BLOCK_KINDS and r.block_id})
    for block_id in block_ids:
        # IDs are data, never filesystem path components selected by an agent.
        path_id = hashlib.sha256(block_id.encode()).hexdigest()[:24]
        block = [r for r in selected if r.block_id == block_id and r.kind in BLOCK_KINDS]
        values = [_record(r) for r in block]
        files[f"blocks/{path_id}/records.json"] = json_bytes(values)
        latest = next((r for r in reversed(block) if r.kind == RecordKind.BLOCK), None)
        objective = public_value(latest.payload.get("start", {}).get("objective", "Unknown objective")) if latest else "Unknown objective"
        status = latest.payload.get("status", "unknown") if latest else "unknown"
        counts = {kind.value: sum(r.kind == kind for r in block) for kind in (RecordKind.MEASUREMENT, RecordKind.EVIDENCE)}
        summary = (f"# Block `{block_id}`\n\n{objective}\n\nLifecycle: {status}. Objective attainment: unknown.\n\n"
                   f"Retained measurements: {counts['measurement']}; admitted evidence records: {counts['evidence']}.\n\n"
                   "Hypotheses, semantic judgments, Director decisions and operational failures retain their own labels in records.json. "
                   "Lifecycle completion and replay do not establish scientific utility.\n")
        contexts = [r for r in block if r.kind == RecordKind.LITERATURE_CONTEXT]
        if contexts:
            categories = sorted({r.payload.get("category", "unknown") for r in contexts})
            context_counts = ", ".join(f"{category}: {sum(r.payload.get('category', 'unknown') == category for r in contexts)}"
                                       for category in categories)
            summary += (f"\nTentative literature context assessments — {context_counts}. "
                        "These are search-bound annotations, not proof of novelty or independent replication. "
                        "Exact claim/source/evidence links, native judgments, coverage limits and unresolved issues are in [records.json](records.json).\n")
        files[f"blocks/{path_id}/summary.md"] = summary.encode()
    readme = ("# OncoJevLab\n\nDeterministic observation of persisted OncoJev research. "
              "This repository grants no orchestration or evidence-admission authority.\n\n"
              f"Renderer: `{RENDERER}`. Populated blocks: {len(block_ids)}.\n\n"
              "Every exported record carries its immutable sequence, typed ID and source payload hash. "
              "Exact acquired bytes, credentials and private execution environments are omitted. "
              "Exported notebook edits are never ingested into scientific state.\n")
    files["README.md"] = readme.encode()
    identities = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}
    basis = {"renderer": RENDERER, "source_high_water": max((r.seq for r in selected), default=0),
             "registry_revisions": [r.record_id for r in selected if r.kind == RecordKind.REGISTRY_REVISION],
             "files": identities}
    files["manifest.json"] = json_bytes({**basis, "export_sha256": content_hash(basis)})
    return files


def retain_export(store, *, cause):
    from src.persistence.records import StoredRecord
    from uuid import uuid4
    files = render_snapshot(store)
    manifest = json.loads(files['manifest.json'])
    existing = store.records(kind=RecordKind.EXPORT)
    if existing and existing[-1].payload.get('export_sha256') == manifest['export_sha256']:
        return existing[-1]
    return store.append(StoredRecord(kind=RecordKind.EXPORT, record_id=str(uuid4()),
        payload={**manifest, 'cause': cause, 'authority': 'downstream_projection_only'}))


def write_snapshot(files, destination):
    root = Path(destination).resolve()
    root.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        target = root / name
        if not target.resolve().is_relative_to(root) or any(p.is_symlink() for p in (target, *target.parents)):
            raise ValueError("export path escaped or contains links")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
