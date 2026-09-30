"""Append-only SQLite store for typed research records.

The store exposes insert and read only. Database triggers reject every update
and delete, so append-only history is a storage-level invariant rather than a
convention. No domain policy lives here.
"""

from __future__ import annotations

from pathlib import Path
import json
import sqlite3

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


class SqliteResearchStore:
    def __init__(self, path: str | Path = ":memory:") -> None:
        self._connection = sqlite3.connect(str(path), check_same_thread=False)
        self._connection.executescript(_SCHEMA)
        self._connection.commit()

    def append(self, record: StoredRecord) -> StoredRecord:
        cursor = self._connection.execute(
            "INSERT INTO records (kind, block_id, record_id, recorded_at, schema_version, payload) VALUES (?, ?, ?, ?, ?, ?)",
            (
                record.kind.value,
                record.block_id,
                record.record_id,
                record.recorded_at.isoformat(),
                record.schema_version,
                json.dumps(record.payload, sort_keys=True, default=str),
            ),
        )
        self._connection.commit()
        return record.model_copy(update={"seq": int(cursor.lastrowid)})

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
        rows = self._connection.execute(
            f"SELECT seq, kind, block_id, record_id, recorded_at, schema_version, payload FROM records{where} ORDER BY seq",
            parameters,
        ).fetchall()
        return tuple(self._row_to_record(row) for row in rows)

    def latest(self, kind: RecordKind, *, block_id: str | None = None) -> StoredRecord | None:
        matches = self.records(kind=kind, block_id=block_id)
        return matches[-1] if matches else None

    def block_ids(self) -> tuple[str, ...]:
        rows = self._connection.execute(
            "SELECT DISTINCT block_id FROM records WHERE block_id IS NOT NULL ORDER BY block_id"
        ).fetchall()
        return tuple(row[0] for row in rows)

    def count(self) -> int:
        return int(self._connection.execute("SELECT COUNT(*) FROM records").fetchone()[0])

    def close(self) -> None:
        self._connection.close()

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
