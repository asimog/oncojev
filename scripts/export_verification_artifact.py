"""Export the available historical live ledger using a fixed redaction allowlist."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "var/phase3-live/stdout-2.json"
TARGET = ROOT / "src/oncolab/proven/artifacts/initial-live-validation-2026-09-30.json"
FIELDS = {"capability_id", "endpoint", "acquisition_id", "records", "analysis_id", "method",
          "evidence_id", "artifact_id", "sha256", "status", "block_id", "resolved_models"}


def main():
    original = SOURCE.read_bytes()
    value = json.loads(original)
    artifact = {"format": "redacted-ledger-v1", "block_id": value["block_id"],
                "source_path": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
                "source_sha256_before_redaction": hashlib.sha256(original).hexdigest(),
                "redaction": "Fixed payload allowlist; output prose, queries, provider messages and completion narrative omitted.",
                "limitations": ["Only the recorded ledger is available; exact acquisitions, numeric inputs, measurements and SVG bytes are absent.",
                                "Historical admission events do not independently certify source-bound evidence or scientific validity."],
                "events": [{"event_type": e["event_type"], "event_id": e.get("event_id"), "occurred_at": e.get("occurred_at"),
                            "payload": {k: v for k, v in e.get("payload", {}).items() if k in FIELDS}}
                           for e in value["events"]]}
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_bytes((json.dumps(artifact, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(hashlib.sha256(TARGET.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
