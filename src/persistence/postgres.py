"""PostgreSQL append-only records, matching SQLite envelopes and sequence refs."""
from contextlib import contextmanager
import json
import threading

import psycopg

from src.persistence.records import StoredRecord
from src.persistence.store import RecordReads


SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
 seq BIGSERIAL PRIMARY KEY, kind TEXT NOT NULL, block_id TEXT,
 record_id TEXT NOT NULL, recorded_at TEXT NOT NULL,
 schema_version TEXT NOT NULL, payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS records_block_idx ON records(block_id);
CREATE INDEX IF NOT EXISTS records_kind_idx ON records(kind);
CREATE OR REPLACE FUNCTION reject_record_mutation() RETURNS trigger AS $$
BEGIN RAISE EXCEPTION 'records are append-only'; END;
$$ LANGUAGE plpgsql;
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='records_no_mutation' AND tgrelid='records'::regclass) THEN
  CREATE TRIGGER records_no_mutation BEFORE UPDATE OR DELETE ON records
  FOR EACH ROW EXECUTE FUNCTION reject_record_mutation();
 END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='records_no_truncate' AND tgrelid='records'::regclass) THEN
  CREATE TRIGGER records_no_truncate BEFORE TRUNCATE ON records
  FOR EACH STATEMENT EXECUTE FUNCTION reject_record_mutation();
 END IF;
END $$;
"""


class PostgresResearchStore(RecordReads):
    def __init__(self, url, *, initialize=False):
        self.path = None  # Database disk is owned by the separate service.
        self._lock = threading.RLock()
        self._transaction_depth = 0
        self._connection = psycopg.connect(url, autocommit=True, connect_timeout=10,
                                         options="-c statement_timeout=30000 -c lock_timeout=10000")
        if initialize:
            with self._connection.transaction():
                self._connection.execute(SCHEMA)
        self._connection.execute("SELECT seq FROM records LIMIT 1")

    @contextmanager
    def transaction(self):
        with self._lock:
            outer = self._transaction_depth == 0
            self._transaction_depth += 1
            try:
                if outer:
                    with self._connection.transaction():
                        yield
                else:
                    yield
            finally:
                self._transaction_depth -= 1

    def _query(self, query, parameters=()):
        # Shared read queries are internal static SQL; record values stay bound.
        return self._connection.execute(query.replace("?", "%s"), parameters)

    def append(self, record: StoredRecord):
        return self.append_many((record,))[0]

    def append_many(self, records):
        with self.transaction():
            # Serialize sequence assignment through commit across producer and
            # downstream receipt processes, preserving immutable prefix pins.
            self._connection.execute("SELECT pg_advisory_xact_lock(794338921)")
            saved = []
            for record in records:
                seq = self._connection.execute(
                    "INSERT INTO records(kind,block_id,record_id,recorded_at,schema_version,payload) "
                    "VALUES (%s,%s,%s,%s,%s,%s) RETURNING seq",
                    (record.kind.value, record.block_id, record.record_id, record.recorded_at.isoformat(),
                     record.schema_version, json.dumps(record.payload, sort_keys=True, default=str)),
                ).fetchone()[0]
                saved.append(record.model_copy(update={"seq": seq}))
            return tuple(saved)

    def close(self):
        self._connection.close()


def open_store(path):
    import os
    from src.persistence.store import SqliteResearchStore
    url = os.environ.get("ONCOJEV_DATABASE_URL")
    return PostgresResearchStore(url) if url else SqliteResearchStore(path)
