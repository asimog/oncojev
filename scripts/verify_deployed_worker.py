"""Retain actual Railway boundary observations without claiming full H11 proof."""
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from uuid import uuid4

from src.oncolab.institution import application_identity
from src.persistence.records import RecordKind, StoredRecord
from src.persistence.postgres import open_store
from src.runtime.paths import data_root


def main():
    if not os.environ.get("RAILWAY_SERVICE_ID") or os.getuid() == 0:
        raise RuntimeError("run this verifier as the actual nonroot Railway worker user")
    root = Path(__file__).resolve().parents[1]
    results = {}
    for name in ("verify_coder_container", "verify_local_science"):
        completed = subprocess.run([sys.executable, str(root / "scripts" / (name + ".py"))],
            check=True, capture_output=True, text=True, timeout=90)
        results[name] = json.loads(completed.stdout.splitlines()[-1])
    payload = {"status": "partial", "target": "railway", "application_identity": application_identity(),
        "service_id": os.environ["RAILWAY_SERVICE_ID"], "environment_id": os.environ["RAILWAY_ENVIRONMENT_ID"],
        "platform": platform.platform(), "worker_uid": os.getuid(), "boundary_checks": results,
        "service_confinement_complete": False,
        "limitations": ["Aggregate Coder process/disk controls and API responsiveness under heavy science remain unqualified.",
                        "Fixture scientific transport proves execution confinement, not public method utility.",
                        "Restart recovery and sequential scientific cycles require separate source-linked observations."]}
    with_store = open_store(data_root(root) / "oncojev.sqlite3")
    try:
        stored = with_store.append(StoredRecord(kind=RecordKind.DEPLOYMENT_VERIFICATION,
            record_id=str(uuid4()), payload=payload))
        print(json.dumps({"record_id": stored.record_id, "seq": stored.seq, **payload}))
    finally:
        with_store.close()


if __name__ == "__main__":
    main()
