"""Downstream Git publisher; called only by a separate credential-owning process."""
import json
from pathlib import Path
import subprocess
from uuid import uuid4

from src.application.export import write_snapshot
from src.persistence.records import RecordKind, StoredRecord


def publish_snapshot(store, files, checkout):
    manifest = json.loads(files["manifest.json"])
    identity = manifest["export_sha256"]
    attempts = [r for r in store.records(kind=RecordKind.PUBLICATION)
                if r.payload.get("export_sha256") == identity]
    successful = [r for r in attempts if r.payload.get("status") == "published"]
    if successful:
        return successful[-1].payload
    if len(attempts) >= 3:
        return {**attempts[-1].payload, "retry_exhausted": True}
    root = Path(checkout).resolve()
    payload = {"export_sha256": identity, "renderer": manifest["renderer"],
               "source_high_water": manifest["source_high_water"], "target": "asimog/oncojevlab"}
    def git(*arguments):
        return subprocess.run(["git", "-C", str(root), *arguments], check=True,
                              capture_output=True, text=True, timeout=60).stdout.strip()
    try:
        remote = git("remote", "get-url", "origin")
        if remote not in {"https://github.com/asimog/oncojevlab.git", "git@github.com:asimog/oncojevlab.git"}:
            raise ValueError("publisher checkout must target the approved separate notebook repository")
        if git("status", "--porcelain"):
            raise ValueError("publisher requires a clean checkout; preserve external notebook edits")
        old = {}
        previous = root / "manifest.json"
        if previous.exists():
            old = json.loads(previous.read_text(encoding="utf-8"))
            for name in old.get("files", {}):
                if name in files:
                    continue
                target = root / name
                if not target.resolve().is_relative_to(root) or any(p.is_symlink() for p in (target, *target.parents)):
                    raise ValueError("previous export path escaped or contains links")
                if target.is_file():
                    target.unlink()
        write_snapshot(files, root)
        git("add", "--", *sorted(set(files) | set(old.get("files", {}))))
        if git("diff", "--cached", "--name-only"):
            git("commit", "-m", "OncoJev snapshot " + identity[:12])
        commit = git("rev-parse", "HEAD")
        git("push", "origin", "HEAD:main")
        remote_sha = git("ls-remote", "origin", "refs/heads/main").split()[0]
        if remote_sha != commit:
            raise RuntimeError("publisher remote SHA does not match generated commit")
        payload.update(status="published", commit_sha=commit)
    except Exception as error:
        # Error types retain outcome without persisting Git credential URLs or
        # stderr. No scientific finalization participates in this transaction.
        payload.update(status="failed", error_type=type(error).__name__)
    store.append(StoredRecord(kind=RecordKind.PUBLICATION, record_id=str(uuid4()), payload=payload))
    return payload
