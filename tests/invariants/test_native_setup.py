"""Developer setup reuse is disposable and independent of scientific qualification."""
import subprocess
import sys
from pathlib import Path
import venv

import pytest

from scripts.verify_native import prepare_dependencies, prepare_tree


@pytest.fixture
def checkout(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
    for name, content in {"src/owner.py": "value = 1\n", "scripts/probe.py": "print('proof')\n",
                          "config/runtime.yaml": "limit: 1\n", "pyproject.toml": "[project]\n",
                          "uv.lock": "version = 1\n"}.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    return root


def test_native_copy_carries_governance_inputs_without_historical_context(checkout, tmp_path):
    current = {"architecture.yaml", ".rgignore", "web/app/page.tsx", "tests/test_owner.py"}
    excluded = {"docs/Archive/old.md", ".upstream/manifest.yaml"}
    for name in current | excluded:
        path = checkout / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n")
    tree, reused = prepare_tree(checkout, tmp_path / "cache")
    assert not reused
    assert all((tree / name).read_text() == "fixture\n" for name in current)
    assert all(not (tree / name).exists() for name in excluded)
    for name in excluded:
        (checkout / name).write_text("historical change\n")
    assert prepare_tree(checkout, tmp_path / "cache") == (tree, True)


@pytest.mark.parametrize("change", ["source", "config", "probe", "new-file", "deleted-file", "damaged-copy"])
def test_native_tree_reuses_exact_bytes_and_invalidates_changes(checkout, tmp_path, change):
    cache = tmp_path / "cache"
    first, reused = prepare_tree(checkout, cache)
    assert not reused
    marker = first / "src/owner.py"
    original_time = marker.stat().st_mtime_ns
    again, reused = prepare_tree(checkout, cache)
    assert reused and again == first
    assert marker.stat().st_mtime_ns == original_time
    target = {"source": checkout / "src/owner.py", "config": checkout / "config/runtime.yaml",
              "probe": checkout / "scripts/probe.py", "new-file": checkout / "src/new.py",
              "deleted-file": checkout / "src/owner.py", "damaged-copy": marker}[change]
    if change == "deleted-file":
        # Track the file so deletion is represented in the real Git inventory.
        subprocess.run(["git", "-C", str(checkout), "add", "src/owner.py"], check=True)
        target.unlink()
    else:
        target.write_text("changed\n")
    replacement, reused = prepare_tree(checkout, cache)
    assert not reused and replacement != first
    if change == "deleted-file":
        assert not (replacement / "src/owner.py").exists()
    elif change == "damaged-copy":
        assert (replacement / "src/owner.py").read_text() == "value = 1\n"
    else:
        assert (replacement / target.relative_to(checkout)).read_text() == "changed\n"
    assert prepare_tree(checkout, cache) == (replacement, True)


def test_native_dependencies_reuse_lock_and_environment_but_never_failed_sync(checkout, tmp_path, monkeypatch):
    from scripts import verify_native

    developer = tmp_path / "developer-venv"
    venv.EnvBuilder(with_pip=False).create(developer)
    python = developer / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    site = Path(subprocess.run([str(python), "-I", "-c",
                               "import sysconfig; print(sysconfig.get_path('purelib'))"],
                              check=True, capture_output=True, text=True).stdout.strip())
    package = site / "fixture.py"
    package.write_text("value = 1\n")
    metadata = site / "fixture-1.0.dist-info"
    metadata.mkdir()
    (metadata / "METADATA").write_text("Name: fixture\nVersion: 1.0\n")
    (metadata / "RECORD").write_text("fixture.py,,\nfixture-1.0.dist-info/METADATA,,\n")
    cache = tmp_path / "cache"
    tree, _ = prepare_tree(checkout, cache)
    real_run = subprocess.run
    installs = []
    fail = False

    def transport(command, **kwargs):
        if command[0] != "fixture-uv":
            return real_run(command, **kwargs)
        installs.append(command)
        if fail:
            raise subprocess.CalledProcessError(1, command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(verify_native.subprocess, "run", transport)
    assert not prepare_dependencies(tree, cache, python, "fixture-uv")
    assert prepare_dependencies(tree, cache, python, "fixture-uv")
    assert len(installs) == 1
    # Source-only changes refresh the tree, without reinstalling dependencies.
    (checkout / "src/owner.py").write_text("value = 2\n")
    tree, _ = prepare_tree(checkout, cache)
    assert prepare_dependencies(tree, cache, python, "fixture-uv")
    (checkout / "uv.lock").write_text("version = 2\n")
    tree, _ = prepare_tree(checkout, cache)
    fail = True
    with pytest.raises(subprocess.CalledProcessError):
        prepare_dependencies(tree, cache, python, "fixture-uv")
    assert "environment" not in verify_native.read_state(cache / "dependencies.json")
    fail = False
    assert not prepare_dependencies(tree, cache, python, "fixture-uv")
    # Package bytes can drift without any version/RECORD change.
    package.write_text("value = 2\n")
    fail = True
    with pytest.raises(subprocess.CalledProcessError):
        prepare_dependencies(tree, cache, python, "fixture-uv")
    fail = False
    assert not prepare_dependencies(tree, cache, python, "fixture-uv")
    assert "--reinstall" in installs[-1]
    # Observed interpreter, kernel and package metadata invalidate the setup marker.
    observe = verify_native.environment_snapshot
    observed = observe(python)
    for field in ("version", "interpreter", "platform", "packages"):
        changed = {**observed, field: "changed observation"}
        monkeypatch.setattr(verify_native, "environment_snapshot", lambda python: changed)
        assert not prepare_dependencies(tree, cache, python, "fixture-uv")
        assert prepare_dependencies(tree, cache, python, "fixture-uv")
    assert len(installs) == 9
    # Losing non-canonical cache state only forces setup; no evidence is deleted.
    (cache / "dependencies.json").write_text("broken json")
    assert not prepare_dependencies(tree, cache, python, "fixture-uv")
