from collections.abc import Iterable
from pathlib import Path
from uuid import uuid4
import hashlib
import base64
import json
import re
from typing import Literal

from pydantic import BaseModel, Field
import yaml
from src.oncolab.models import OncoLabDescriptor, OncoLabKind, OncoLabCard, OncoLabPage
from src.provenance import content_hash
from src.oncolab.execution import ROUTES
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
    snapshot_id: str | None = None
    oncolab_registry_revision: str | None = None
    oncolab_history_high_water: int | None = None
    application_identity: str | None = None
    retrieval_version: str | None = None
    continuation: str | None = None
    contract_hashes: dict[str, str] = Field(default_factory=dict)


class OncoLabIndex:
    """The one shared OncoLab domain index for Director and Researcher.

    It combines bounded catalogue lookup with records of verified execution.
    The Pydantic AI runtime is only a client through dependencies.
    """

    max_results = 20

    def __init__(self, descriptors: Iterable[OncoLabDescriptor], *, routes=None, revision_id=None, history_high_water=None) -> None:
        items = tuple(descriptors)
        ids = [descriptor.capability_id for descriptor in items]
        if len(ids) != len(set(ids)):
            raise ValueError("capability IDs must be unique")
        self._items = tuple(sorted(items, key=lambda descriptor: descriptor.capability_id))
        self._by_id = {descriptor.capability_id: descriptor for descriptor in self._items}
        self._verification_records: dict[str, list[OncoLabVerificationRecord]] = {}
        self.routes = dict(ROUTES if routes is None else routes)
        self.revision_id = revision_id
        self.history_high_water = history_high_water

    def descriptors(self):
        return tuple(d.model_copy(deep=True) for d in self._items)

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

    @property
    def snapshot_id(self) -> str:
        return content_hash([d.model_dump(mode="json") for d in self._items])

    def card(self, descriptor: OncoLabDescriptor) -> OncoLabCard:
        data = {"purpose": descriptor.purpose, "applicability": descriptor.applicability,
                "input_summary": descriptor.input_contract}
        return OncoLabCard(capability_id=descriptor.capability_id, name=descriptor.name[:120], kind=descriptor.kind,
            tags=tuple(t[:64] for t in descriptor.tags[:12]), limitations=tuple(s[:240] for s in descriptor.limitations[:3]),
            availability=descriptor.availability, execution_mode=descriptor.execution_mode, access_policy=descriptor.access_policy,
            contract_sha256=content_hash(descriptor.model_dump(mode="json")),
            truncated=any(len(v)>320 for v in data.values()) or len(descriptor.tags)>12 or len(descriptor.limitations)>3 or len(descriptor.name)>120 or any(len(t)>64 for t in descriptor.tags)
                      or any(len(v)>240 for v in descriptor.limitations),
            **{k:v[:320] for k,v in data.items()})

    def search_page(self, query: str = "", *, kinds=(), tags=(), limit: int = 8, continuation: str | None = None) -> OncoLabPage:
        """Progressive high-recall discovery. Zero-overlap candidates remain browsable.

        Cursor binds query/filters and snapshot; changing contracts invalidates it.
        Each response remains bounded regardless of catalogue capacity.
        """
        if not 1 <= limit <= self.max_results or len(query)>4000:
            raise ValueError("invalid search bound")
        identity = content_hash({"query":query, "kinds":sorted(map(str,kinds)), "tags":sorted(tags), "snapshot":self.snapshot_id,
                                 "registry_revision": self.revision_id, "history_high_water": self.history_high_water})
        offset = 0
        if continuation:
            try:
                cursor=json.loads(base64.urlsafe_b64decode(continuation))
                if cursor["identity"] != identity or not isinstance(cursor["offset"],int) or cursor["offset"]<0:
                    raise ValueError("stale or changed search cursor")
                offset=cursor["offset"]
            except (ValueError, KeyError, TypeError) as error:
                raise ValueError("invalid continuation") from error
        def terms(text):
            return set(re.findall(r"[a-z0-9]+",text.lower()))
        wanted=terms(query)
        ranked=[]
        for d in self._items:
            if kinds and d.kind not in kinds or tags and not set(t.lower() for t in tags).issubset(t.lower() for t in d.tags):
                continue
            text=" ".join((d.name,d.purpose,d.input_contract,d.output_contract,d.applicability,*d.tags))
            ranked.append((len(wanted & terms(text)),d))
        ranked.sort(key=lambda pair:(-pair[0],pair[1].capability_id))
        end=min(offset+limit,len(ranked))
        cursor=base64.urlsafe_b64encode(json.dumps({"identity":identity,"offset":end},separators=(",",":")).encode()).decode() if end<len(ranked) else None
        return OncoLabPage(cards=tuple(self.card(d) for _,d in ranked[offset:end]),snapshot_id=self.snapshot_id,
                          oncolab_registry_revision=self.revision_id, oncolab_history_high_water=self.history_high_water,
                          continuation=cursor,exhausted=cursor is None,total_candidates=len(ranked))

    def describe_with_verification(self, capability_id: str) -> dict[str, object] | None:
        """Return one bounded agent-safe view of a descriptor and its verification history."""
        descriptor = self.describe(capability_id)
        if descriptor is None:
            return None
        records = self.verification_records(capability_id)
        return {
            "descriptor": descriptor.model_dump(mode="json"),
            "contract_sha256": content_hash(descriptor.model_dump(mode="json")),
            "execution_routes": [r.model_dump(mode="json") for r in self.routes.get(capability_id, ())],
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
