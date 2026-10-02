"""Bounded developer setup for native probes; cache entries are never qualification."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from uuid import uuid4


TREES = {"src", "config", "scripts", "skills", "docs", "tests", "web"}
FILES = {"README.md", "AGENTS.md", "pyproject.toml", "uv.lock", "railway.toml",
         "architecture.yaml", ".rgignore"}
PROBES = {"coder": "verify_coder_container", "coder-resources": "verify_coder_resources",
          "science": "verify_local_science", "science-resources": "verify_science_resources",
          "architecture": "check_architecture"}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def inventory(root):
    paths = subprocess.run(["git", "-C", str(root), "ls-files", "--cached", "--others",
                            "--exclude-standard", "-z"], check=True, capture_output=True,
                           timeout=10).stdout.decode().split("\0")
    result = {}
    for name in sorted(set(paths) - {""}):
        if ".upstream" in Path(name).parts or Path(name).parts[:2] == ("docs", "Archive"):
            continue
        path = root / name
        if name not in FILES and Path(name).parts[0] not in TREES:
            continue
        if path.is_symlink():
            raise RuntimeError(f"native setup does not copy symlinks: {name}")
        if path.is_file():
            result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def tree_matches(root, expected):
    if not root.is_dir() or root.is_symlink():
        return False
    actual = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            return False
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            actual[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return actual == expected


def read_state(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def write_state(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True))
    temporary.replace(path)


def prepare_tree(source, cache):
    source, cache = Path(source).resolve(), Path(cache).resolve()
    expected = inventory(source)
    key = digest(expected)
    cache.mkdir(parents=True, exist_ok=True)
    stamp = cache / "tree.json"
    previous = read_state(stamp)
    if previous and previous.get("identity") == key:
        tree = cache / previous.get("directory", "")
        if tree.parent == cache and tree_matches(tree, expected):
            return tree, True
    # New directories also handle damaged entries; never erase an old proof tree.
    tree = Path(tempfile.mkdtemp(prefix="tree-", dir=cache))
    for name in expected:
        destination = tree / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / name, destination)
    if not tree_matches(tree, expected) or inventory(source) != expected:
        raise RuntimeError("source changed during native setup; retry")
    write_state(stamp, {"identity": key, "directory": tree.name})
    return tree, False


def environment_snapshot(python):
    code = """
import hashlib, importlib.metadata, json, platform, sys
from pathlib import Path
distributions = list(importlib.metadata.distributions())
contents = hashlib.sha256()
for distribution in sorted(distributions, key=lambda d: d.metadata['Name']):
 for relative in sorted(distribution.files or [], key=str):
  if '__pycache__' in relative.parts or relative.suffix == '.pyc': continue
  path = distribution.locate_file(relative)
  contents.update(str(path).encode())
  contents.update(hashlib.sha256(path.read_bytes()).digest() if path.is_file() else b'missing')
print(json.dumps({'executable': sys.executable, 'prefix': sys.prefix,
 'base_prefix': sys.base_prefix, 'version': sys.version, 'platform': platform.platform(),
 'interpreter': hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest(),
 'packages': sorted((d.metadata['Name'], d.version,
    hashlib.sha256((d.read_text('RECORD') or '').encode()).hexdigest())
    for d in distributions), 'package_bytes': contents.hexdigest()}))
"""
    result = subprocess.run([str(python), "-I", "-c", code], check=True,
                            capture_output=True, text=True, timeout=10)
    return json.loads(result.stdout)


def prepare_dependencies(tree, cache, python, uv):
    stamp = Path(cache) / "dependencies.json"
    basis = {name: hashlib.sha256((tree / name).read_bytes()).hexdigest()
             for name in ("pyproject.toml", "uv.lock")}
    observed = environment_snapshot(python)
    if observed["prefix"] == observed["base_prefix"]:
        raise RuntimeError("native developer setup requires an existing venv, not system Python")
    previous = read_state(stamp)
    if previous == {"basis": basis, "environment": observed}:
        return True
    environment = os.environ.copy()
    environment["UV_PROJECT_ENVIRONMENT"] = observed["prefix"]
    command = [str(uv), "sync", "--frozen", "--no-dev", "--no-install-project",
               "--python", str(python)]
    old_bytes = (previous or {}).get("environment", {}).get("package_bytes")
    reinstall = bool((previous or {}).get("pending_reinstall")) or (
        old_bytes is not None and old_bytes != observed["package_bytes"])
    # Invalidate before sync, retaining repair intent across failed attempts.
    write_state(stamp, {"pending_reinstall": reinstall})
    if reinstall:
        command.append("--reinstall")
    subprocess.run(command, cwd=tree, env=environment,
                   check=True, timeout=45)
    write_state(stamp, {"basis": basis, "environment": environment_snapshot(python)})
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True, help="Existing developer Linux venv interpreter")
    parser.add_argument("--uv", type=Path, required=True)
    parser.add_argument("--probe", choices=PROBES, action="append", required=True)
    args = parser.parse_args()
    if sys.platform != "linux":
        parser.error("run explicitly inside Linux/WSL; fast tests never launch WSL")
    if str(args.cache.resolve()).startswith("/mnt/"):
        parser.error("cache must use native Linux storage")
    # Serialize shared developer setup; qualification experiments do not use this cache.
    import fcntl
    args.cache.mkdir(parents=True, exist_ok=True)
    with (args.cache / "setup.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error("native setup already in use; retry after it finishes")
        tree, reused_tree = prepare_tree(args.source, args.cache)
        reused_dependencies = prepare_dependencies(tree, args.cache, args.python, args.uv)
        print(json.dumps({"tree": str(tree), "tree_reused": reused_tree,
                          "dependencies_reused": reused_dependencies,
                          "scope": "developer setup only; no qualification reuse"}), flush=True)
        environment = os.environ.copy()
        environment.update(LOGFIRE_SEND_TO_LOGFIRE="false", PYTHONDONTWRITEBYTECODE="1",
                           ONCOJEV_DATA_ROOT=str(args.cache.resolve() / "runs" / uuid4().hex))
        for probe in dict.fromkeys(args.probe):
            subprocess.run([str(args.python), "-B", "-m", "scripts." + PROBES[probe]],
                           cwd=tree, env=environment, check=True, timeout=60)


if __name__ == "__main__":
    main()
