from collections.abc import Iterable
from pathlib import Path
from uuid import uuid4
import hashlib
from typing import Literal

from pydantic import BaseModel, Field
import yaml
from src.oncolab.models import OncoLabDescriptor, OncoLabKind
from src.provenance import ExecutionReference


class OncoLabVerificationRecord(BaseModel, frozen=True):
    capability_id: str
    verification_id: str
    execution_reference: ExecutionReference
    execution_scope: str = Field(min_length=1)
    outcome: Literal["execution_observed", "measurement_validated", "artifact_created"] = "execution_observed"
    source_reference: str = ".upstream/INDEX.md"
    evidence: tuple[str, ...] = Field(min_length=1)


class IndexReceipt(BaseModel, frozen=True):
    receipt_id: str = Field(default_factory=lambda: str(uuid4()))
    actor: str
    operation: str
    query: str = ""
    kinds: tuple[OncoLabKind, ...] = ()
    tags: tuple[str, ...] = ()
    requested_limit: int | None = None
    effective_limit: int | None = None
    returned_ids: tuple[str, ...] = ()
    selected_id: str | None = None
    requested_id: str | None = None
    block_id: str | None = None
    mission_id: str | None = None
    cycle_id: str | None = None


class OncoLabIndex:
    """The one shared OncoLab domain index for Director and Researcher.

    It combines bounded catalogue lookup with records of verified execution.
    The Pydantic AI runtime is only a client through dependencies.
    """

    max_results = 20

    def __init__(self, descriptors: Iterable[OncoLabDescriptor]) -> None:
        items = tuple(descriptors)
        ids = [descriptor.capability_id for descriptor in items]
        if len(ids) != len(set(ids)):
            raise ValueError("capability IDs must be unique")
        self._items = tuple(sorted(items, key=lambda descriptor: descriptor.capability_id))
        self._by_id = {descriptor.capability_id: descriptor for descriptor in self._items}
        self._verification_records: dict[str, list[OncoLabVerificationRecord]] = {}

    def search(self, query: str = "", *, kinds: Iterable[OncoLabKind] = (), tags: Iterable[str] = (), limit: int = 8) -> tuple[OncoLabDescriptor, ...]:
        if not 1 <= limit <= self.max_results:
            raise ValueError(f"limit must be between 1 and {self.max_results}")
        requested_kinds = frozenset(kinds)
        requested_tags = frozenset(tag.lower() for tag in tags)
        query_terms = frozenset(query.lower().split())

        def score(descriptor: OncoLabDescriptor) -> int:
            if requested_kinds and descriptor.kind not in requested_kinds:
                return -1
            descriptor_tags = frozenset(tag.lower() for tag in descriptor.tags)
            if requested_tags and not requested_tags.issubset(descriptor_tags):
                return -1
            text = " ".join((descriptor.name, descriptor.purpose, *descriptor.tags)).lower()
            return len(query_terms.intersection(text.split()))

        ranked = [(score(descriptor), descriptor) for descriptor in self._items]
        ranked = [match for match in ranked if match[0] >= 0 and (not query_terms or match[0] > 0)]
        ranked.sort(key=lambda match: (-match[0], match[1].capability_id))
        return tuple(descriptor for _, descriptor in ranked[:limit])

    def describe(self, capability_id: str) -> OncoLabDescriptor | None:
        return self._by_id.get(capability_id)

    def describe_with_verification(self, capability_id: str) -> dict[str, object] | None:
        """Return one bounded agent-safe view of a descriptor and its verification history."""
        descriptor = self.describe(capability_id)
        if descriptor is None:
            return None
        records = self.verification_records(capability_id)
        return {
            "descriptor": descriptor.model_dump(mode="json"),
            "verification": [record.model_dump(mode="json") for record in records[-20:]],
            "omitted_verifications": max(0, len(records)-20),
        }

    def count(self) -> int:
        """Return catalogue size without exposing descriptors to an agent prompt."""
        return len(self._items)

    def list_kinds(self) -> tuple[OncoLabKind, ...]:
        return tuple(sorted({descriptor.kind for descriptor in self._items}, key=str))

    def record_verification(self, record: OncoLabVerificationRecord) -> None:
        if record.capability_id not in self._by_id:
            raise ValueError(f"unknown verification capability: {record.capability_id}")
        existing = self._verification_records.setdefault(record.capability_id, [])
        match = next((r for r in existing if r.verification_id == record.verification_id), None)
        if match is not None:
            if match != record:
                raise ValueError("conflicting verification identity")
            return
        existing.append(record.model_copy(deep=True))

    def verification_records(self, capability_id: str) -> tuple[OncoLabVerificationRecord, ...]:
        return tuple(self._verification_records.get(capability_id, ()))

    def load_verification_records(self, directory: Path | None = None) -> "OncoLabIndex":
        """Load bundled verification records into this one application registry."""
        record_directory = directory or Path(__file__).with_name("proven")
        if not record_directory.is_dir():
            return self
        for path in sorted(record_directory.glob("*.yaml")):
            payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            if not isinstance(payload, dict) or not isinstance(payload.get("records", []), list):
                raise ValueError(f"invalid capability verification record: {path}")
            for item in payload["records"]:
                record = OncoLabVerificationRecord.model_validate(item)
                reference = record.execution_reference
                if reference.kind == "file":
                    root = Path(__file__).resolve().parents[2]
                    target = (root / reference.value).resolve()
                    allowed = root / "src" / "oncolab" / "proven" / "artifacts"
                    if not target.is_relative_to(allowed) or not target.is_file():
                        raise ValueError(f"unresolved verification artifact: {reference.value}")
                    if hashlib.sha256(target.read_bytes()).hexdigest() != reference.sha256:
                        raise ValueError(f"verification artifact integrity mismatch: {reference.value}")
                else:
                    raise ValueError("bundled verification must reference a portable file artifact")
                self.record_verification(record)
        return self
