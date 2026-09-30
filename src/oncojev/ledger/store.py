from collections.abc import Iterable

from oncojev.ledger.events import LedgerEvent


class Ledger:
    """Append-only event history. Snapshots cannot mutate internal history."""

    def __init__(self) -> None:
        self._events: list[LedgerEvent] = []

    def append(self, event: LedgerEvent) -> None:
        self._events.append(event.model_copy(deep=True))

    def history(self) -> tuple[LedgerEvent, ...]:
        return tuple(event.model_copy(deep=True) for event in self._events)

    def find(self, event_type: str) -> Iterable[LedgerEvent]:
        return (event for event in self.history() if event.event_type == event_type)
