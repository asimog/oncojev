"""Append-only SQLite store for typed research records.

The store exposes insert and read only. Database triggers reject every update
and delete, so append-only history is a storage-level invariant rather than a
convention. No domain policy lives here.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import json
import sqlite3
import threading

from src.persistence.records import RecordKind, StoredRecord


_SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    block_id TEXT,
    record_id TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS records_block_idx ON records (block_id);
CREATE INDEX IF NOT EXISTS records_kind_idx ON records (kind);
CREATE TRIGGER IF NOT EXISTS records_no_update BEFORE UPDATE ON records
BEGIN SELECT RAISE(ABORT, 'records are append-only'); END;
CREATE TRIGGER IF NOT EXISTS records_no_delete BEFORE DELETE ON records
BEGIN SELECT RAISE(ABORT, 'records are append-only'); END;
"""


class RecordReads:
    def high_water(self) -> int:
        with self._lock:
            return int(self._query("SELECT COALESCE(MAX(seq), 0) FROM records").fetchone()[0])

    def records(
        self, *, kind: RecordKind | None = None, block_id: str | None = None
    ) -> tuple[StoredRecord, ...]:
        clauses: list[str] = []
        parameters: list[str] = []
        if kind is not None:
            clauses.append("kind = ?")
            parameters.append(kind.value)
        if block_id is not None:
            clauses.append("block_id = ?")
            parameters.append(block_id)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._lock:
            rows = self._query(
                f"SELECT seq, kind, block_id, record_id, recorded_at, schema_version, payload FROM records{where} ORDER BY seq",
                parameters,
            ).fetchall()
        return tuple(self._row_to_record(row) for row in rows)

    def latest(self, kind: RecordKind, *, block_id: str | None = None) -> StoredRecord | None:
        where = "kind = ?" + (" AND block_id = ?" if block_id is not None else "")
        parameters = [kind.value] + ([block_id] if block_id is not None else [])
        with self._lock:
            row = self._query(
                f"SELECT seq, kind, block_id, record_id, recorded_at, schema_version, payload FROM records WHERE {where} ORDER BY seq DESC LIMIT 1",
                parameters,
            ).fetchone()
        return self._row_to_record(row) if row else None

    def record_at(self, seq: int) -> StoredRecord | None:
        """Resolve an immutable sequence reference without scanning whole history."""
        with self._lock:
            row = self._query(
                "SELECT seq, kind, block_id, record_id, recorded_at, schema_version, payload FROM records WHERE seq = ?", (seq,)
            ).fetchone()
        return self._row_to_record(row) if row else None

    def block_ids(self) -> tuple[str, ...]:
        with self._lock:
            rows = self._query(
                "SELECT DISTINCT block_id FROM records WHERE block_id IS NOT NULL ORDER BY block_id"
            ).fetchall()
        return tuple(row[0] for row in rows)

    def count(self) -> int:
        with self._lock:
            return int(self._query("SELECT COUNT(*) FROM records").fetchone()[0])


    @staticmethod
    def _row_to_record(row: sqlite3.Row | tuple) -> StoredRecord:
        seq, kind, block_id, record_id, recorded_at, schema_version, payload = row
        return StoredRecord(
            seq=seq,
            kind=RecordKind(kind),
            block_id=block_id,
            record_id=record_id,
            recorded_at=recorded_at,
            schema_version=schema_version,
            payload=json.loads(payload),
        )


class SqliteResearchStore(RecordReads):
    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = Path(path).resolve() if str(path) != ":memory:" else None
        self._connection = sqlite3.connect(str(path), check_same_thread=False)
        self._lock = threading.RLock()
        self._transaction_depth = 0
        self._connection.executescript(_SCHEMA)
        self._connection.commit()

    @contextmanager
    def transaction(self):
        """Serialize a synchronous owner workflow and commit only its outer boundary."""
        with self._lock:
            outer = self._transaction_depth == 0
            self._transaction_depth += 1
            try:
                yield
            except BaseException:
                if outer:
                    self._connection.rollback()
                raise
            else:
                if outer:
                    self._connection.commit()
            finally:
                self._transaction_depth -= 1

    def append(self, record: StoredRecord) -> StoredRecord:
        return self.append_many((record,))[0]

    def append_many(self, records: tuple[StoredRecord, ...]) -> tuple[StoredRecord, ...]:
        """Commit a terminal bundle atomically, including rollback on append failure."""
        with self.transaction():
            saved = []
            for record in records:
                cursor = self._connection.execute(
                    "INSERT INTO records (kind, block_id, record_id, recorded_at, schema_version, payload) VALUES (?, ?, ?, ?, ?, ?)",
                    (record.kind.value, record.block_id, record.record_id,
                     record.recorded_at.isoformat(), record.schema_version,
                     json.dumps(record.payload, sort_keys=True, default=str)),
                )
                saved.append(record.model_copy(update={"seq": int(cursor.lastrowid)}))
        return tuple(saved)

    def _query(self, query, parameters=()):
        return self._connection.execute(query, parameters)

    def close(self) -> None:
        self._connection.close()
