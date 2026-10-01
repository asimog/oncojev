"""Resolve typed references without executing research or admitting evidence."""

from pathlib import Path
import hashlib

from src.persistence.records import RecordKind
from src.provenance import ExecutionReference, content_hash


def resolve_reference(store, reference: ExecutionReference):
    if reference.kind == "file":
        root = Path(__file__).resolve().parents[2]
        target = (root / reference.value).resolve()
        allowed = root / "src" / "oncolab" / "proven" / "artifacts"
        if not target.is_relative_to(allowed) or not target.is_file():
            raise ValueError("unresolved portable verification reference")
        if hashlib.sha256(target.read_bytes()).hexdigest() != reference.sha256:
            raise ValueError("verification artifact integrity mismatch")
        return {"path": reference.value, "sha256": reference.sha256}
    kind = RecordKind(reference.kind)
    matches = [record.payload for record in store.records(kind=kind, block_id=reference.block_id)
               if record.record_id == reference.value and content_hash(record.payload) == reference.sha256]
    if not matches:
        raise ValueError(f"unresolved {reference.kind} reference: {reference.value}")
    return matches[-1]
