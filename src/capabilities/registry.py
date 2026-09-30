from collections.abc import Iterable

from pydantic import BaseModel, Field
from src.capabilities.models import CapabilityDescriptor, CapabilityKind


class ProvenCapabilityRecord(BaseModel, frozen=True):
    capability_id: str
    verification_id: str
    execution_reference: str
    source_reference: str = ".upstream/INDEX.md"
    evidence: tuple[str, ...] = Field(min_length=1)


class CapabilityRegistry:
    """The one shared laboratory registry for Director and Researcher.

    It combines bounded catalogue lookup with records of verified execution.
    The Pydantic AI runtime is only a client through dependencies.
    """

    max_results = 20

    def __init__(self, descriptors: Iterable[CapabilityDescriptor]) -> None:
        items = tuple(descriptors)
        ids = [descriptor.capability_id for descriptor in items]
        if len(ids) != len(set(ids)):
            raise ValueError("capability IDs must be unique")
        self._items = tuple(sorted(items, key=lambda descriptor: descriptor.capability_id))
        self._by_id = {descriptor.capability_id: descriptor for descriptor in self._items}
        self._proven: dict[str, list[ProvenCapabilityRecord]] = {}

    def search(self, query: str = "", *, kinds: Iterable[CapabilityKind] = (), tags: Iterable[str] = (), limit: int = 8) -> tuple[CapabilityDescriptor, ...]:
        if not 1 <= limit <= self.max_results:
            raise ValueError(f"limit must be between 1 and {self.max_results}")
        requested_kinds = frozenset(kinds)
        requested_tags = frozenset(tag.lower() for tag in tags)
        query_terms = frozenset(query.lower().split())

        def score(descriptor: CapabilityDescriptor) -> int:
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

    def describe(self, capability_id: str) -> CapabilityDescriptor | None:
        return self._by_id.get(capability_id)

    def count(self) -> int:
        """Return catalogue size without exposing descriptors to an agent prompt."""
        return len(self._items)

    def list_kinds(self) -> tuple[CapabilityKind, ...]:
        return tuple(sorted({descriptor.kind for descriptor in self._items}, key=str))

    def record_proven(self, record: ProvenCapabilityRecord) -> None:
        self._proven.setdefault(record.capability_id, []).append(record)

    def proven_records(self, capability_id: str) -> tuple[ProvenCapabilityRecord, ...]:
        return tuple(self._proven.get(capability_id, ()))
