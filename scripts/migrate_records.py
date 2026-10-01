"""Copy an immutable SQLite snapshot to PostgreSQL, preserving every sequence."""
import argparse
import json
import os

from src.persistence.postgres import PostgresResearchStore
from src.persistence.store import SqliteResearchStore
from src.provenance import content_hash


def configure_writer(target, password):
    from psycopg import sql
    if len(password) < 32:
        raise ValueError("a generated writer password is required")
    with target.transaction():
        exists = target._connection.execute("SELECT 1 FROM pg_roles WHERE rolname='oncojev_writer'").fetchone()
        command = "ALTER ROLE oncojev_writer PASSWORD {}" if exists else "CREATE ROLE oncojev_writer LOGIN PASSWORD {}"
        target._connection.execute(sql.SQL(command).format(sql.Literal(password)))
        target._connection.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
        target._connection.execute("GRANT USAGE ON SCHEMA public TO oncojev_writer")
        target._connection.execute("REVOKE ALL ON TABLE records FROM oncojev_writer")
        target._connection.execute("GRANT SELECT, INSERT ON TABLE records TO oncojev_writer")
        target._connection.execute("GRANT USAGE, SELECT ON SEQUENCE records_seq_seq TO oncojev_writer")


def migrate(source, target):
    records = source.records()
    expected = content_hash([r.model_dump(mode="json") for r in records])
    if target.count():
        if content_hash([r.model_dump(mode="json") for r in target.records()]) != expected:
            raise ValueError("nonempty target differs from source; no overwrite or record deletion")
        return {"records": len(records), "snapshot_sha256": expected, "status": "already_migrated"}
    with target.transaction():
        with target._connection.cursor().copy(
            "COPY records(seq,kind,block_id,record_id,recorded_at,schema_version,payload) FROM STDIN"
        ) as copy:
            for record in records:
                copy.write_row((record.seq, record.kind.value, record.block_id, record.record_id,
                                record.recorded_at.isoformat(), record.schema_version,
                                json.dumps(record.payload, sort_keys=True, default=str)))
        if records:
            target._connection.execute("SELECT setval(pg_get_serial_sequence('records','seq'), %s, true)",
                                       (max(r.seq for r in records),))
        actual = content_hash([r.model_dump(mode="json") for r in target.records()])
        if actual != expected:
            raise ValueError("migrated record identities differ; transaction rolled back")
    return {"records": len(records), "snapshot_sha256": expected, "status": "migrated"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    if os.environ.get("ONCOJEV_MAINTENANCE") != "1":
        raise RuntimeError("quiesce the worker before migrating its authoritative snapshot")
    source = SqliteResearchStore(args.source)
    target = PostgresResearchStore(os.environ["ONCOJEV_MIGRATION_DATABASE_URL"], initialize=True)
    try:
        report = migrate(source, target)
        configure_writer(target, os.environ['ONCOJEV_WRITER_PASSWORD'])
        print(json.dumps({**report, "writer_role": "select_insert_only"}))
    finally:
        source.close()
        target.close()


if __name__ == "__main__":
    main()
