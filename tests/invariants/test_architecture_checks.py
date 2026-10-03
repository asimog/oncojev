"""Drift guards operate on checkout artifacts, not application/prose semantics."""
import hashlib
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from scripts.check_architecture import check_documents, check_imports


CHECKER = Path(__file__).resolve().parents[2] / "scripts/check_architecture.py"


@pytest.fixture
def checkout(tmp_path):
    documents = ("README.md", "AGENTS.md", "docs/ARCHITECTURE.md",
                 "docs/IMPLEMENTATION_PLAN.md", "docs/TASK_LOG.md",
                 "docs/PROPOSED_ADR_FAST_LOCAL_TESTING.md")
    for name in documents:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Current owner\n", encoding="utf-8")
    for name in ("src/owner.py", "tests/test_owner.py"):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("raise RuntimeError('must not execute indexed code')\n"
                        "def guard(): pass\ndef test_guard(): pass\n", encoding="utf-8")
    projection = {
        "schema_version": 1, "authority": "projection",
        "canonical_sources": [
            {"path": name, "sha256": hashlib.sha256((tmp_path / name).read_text(encoding="utf-8").encode()).hexdigest()}
            for name in ("AGENTS.md", "docs/ARCHITECTURE.md")],
        "classification": {name: name for name in ("ENFORCED", "TESTED", "REVIEWED")},
        "owners": {"science": {"paths": ["src/owner.py"], "responsibility": "measure",
                               "forbidden": ["allocate"]}},
        "authority_boundaries": [{"owner": "science", "classification": "ENFORCED",
                                  "statement": "scoped guard", "evidence": ["src/owner.py::guard"]}],
        "high_consequence_invariants": [{"owner": "science", "classification": "TESTED",
                                         "statement": "scoped test", "evidence": ["tests/test_owner.py::test_guard"]}],
        "dependency_directions": [{"from": "science", "to": "science"}],
    }
    (tmp_path / "architecture.yaml").write_text(yaml.safe_dump(projection), encoding="utf-8")
    # Excluded files contain both invalid syntax and prohibited planning structures.
    for name in ("docs/Archive/old.md", "docs/Archive/ADR/GUIDANCE.md",
                 "docs/Archive/PREVIOUS_TASK_LOG.md", ".upstream/old.py"):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("## Task 99\nnot python !!!", encoding="utf-8")
    return tmp_path


def run(root):
    return subprocess.run([sys.executable, "-B", str(CHECKER), "--docs-only", "--root", str(root)],
                          capture_output=True, text=True, timeout=10)


def test_valid_projection_is_read_only_and_does_not_execute_evidence(checkout):
    before = {p.relative_to(checkout): p.read_bytes() for p in checkout.rglob("*") if p.is_file()}
    assert run(checkout).returncode == 0
    after = {p.relative_to(checkout): p.read_bytes() for p in checkout.rglob("*") if p.is_file()}
    assert after == before
    # Checkout line endings do not create false stale-source reports.
    for name in ("AGENTS.md", "docs/ARCHITECTURE.md"):
        path = checkout / name
        path.write_bytes(path.read_text(encoding="utf-8").encode().replace(b"\n", b"\r\n"))
    assert run(checkout).returncode == 0


@pytest.mark.parametrize("drift", ["stale", "missing-owner", "missing-symbol", "missing-file",
                                   "excluded", "escape", "unknown-owner", "unknown-class",
                                   "not-test", "canonical", "authority", "flow", "archive-exception-evidence"])
def test_projection_rejects_drift_with_an_actionable_failure(checkout, drift):
    assert run(checkout).returncode == 0
    path = checkout / "architecture.yaml"
    data = yaml.safe_load(path.read_text())
    claim = data["high_consequence_invariants"][0]
    if drift == "stale":
        (checkout / "AGENTS.md").write_text("changed owner rules\n")
    elif drift == "missing-owner":
        data["owners"]["science"]["paths"] = ["src/deleted.py"]
    elif drift in {"missing-symbol", "missing-file", "excluded", "escape", "not-test", "archive-exception-evidence"}:
        claim["evidence"] = [{"missing-symbol": "tests/test_owner.py::deleted",
                              "missing-file": "tests/deleted.py::test_guard",
                              "excluded": "docs/Archive/old.md", "escape": "../outside.py",
                              "archive-exception-evidence": "docs/Archive/ADR/GUIDANCE.md",
                              "not-test": "src/owner.py::guard"}[drift]]
    elif drift == "unknown-owner":
        claim["owner"] = "deleted"
    elif drift == "unknown-class":
        claim["classification"] = "QUALIFIED"
    elif drift == "canonical":
        data["canonical_sources"].pop()
    elif drift == "authority":
        data["authority"] = "canonical"
    else:
        data["dependency_directions"][0]["to"] = "deleted"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    result = run(checkout)
    assert result.returncode == 1
    assert result.stderr and "Traceback" not in result.stderr


@pytest.mark.parametrize("name,content", [
    ("docs/PROPOSED_ADR_FAST_LOCAL_TESTING.md", "## Task 7\n"),
    ("docs/PROPOSED_ADR_FAST_LOCAL_TESTING.md", "## Backlog\n"),
    ("docs/PROPOSED_ADR_FAST_LOCAL_TESTING.md", "- [ ] Implement a capability\n"),
    ("docs/TASK_LOG.md", "Status: blocked\n"), ("docs/TASK_LOG.md", "**Done when: criterion**\n"),
    ("docs/PROPOSED_ADR_FAST_LOCAL_TESTING.md", "[owner](../src/deleted.py)\n"),
    ("docs/PROPOSED_ADR_FAST_LOCAL_TESTING.md", "[section](ARCHITECTURE.md#deleted)\n"),
    ("docs/PROPOSED_ADR_FAST_LOCAL_TESTING.md", "[historical instructions](Archive/old.md)\n"),
    ("docs/PROPOSED_ADR_FAST_LOCAL_TESTING.md", "[historical heading](Archive/ADR/GUIDANCE.md#task-99)\n"),
])
def test_active_documents_reject_broken_navigation_and_planning_structures(checkout, name, content):
    assert run(checkout).returncode == 0
    path = checkout / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    result = run(checkout)
    assert result.returncode == 1
    assert result.stderr and "Traceback" not in result.stderr


def test_plan_owns_structures_while_examples_and_ordinary_prose_are_allowed(checkout):
    (checkout / "docs/IMPLEMENTATION_PLAN.md").write_text("## Task 7\n- [ ] implement\n")
    (checkout / "docs/PROPOSED_ADR_FAST_LOCAL_TESTING.md").write_text("Changed wording; future research is uncertain.\n"
                                       "[current](ARCHITECTURE.md#current-owner)\n"
                                       "```markdown\n## Task 7\n- [ ] example\n```\n")
    assert run(checkout).returncode == 0


@pytest.mark.parametrize("name", ["docs/another-adr.md", "docs/reports/old.md"])
def test_non_current_markdown_must_be_archived(checkout, name):
    assert run(checkout).returncode == 0
    path = checkout / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Untracked extra document\n")
    result = run(checkout)
    assert result.returncode == 1
    assert "archive non-current docs Markdown: " + name in result.stderr


def test_docs_archive_rule_preserves_external_readmes(checkout):
    for name in ("src/science/README.md", "skills/README.md", "evals/README.md", "web/README.md"):
        path = checkout / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Component documentation\n")
    before = {p.relative_to(checkout): p.read_bytes() for p in checkout.rglob("README.md")}
    assert run(checkout).returncode == 0
    assert {p.relative_to(checkout): p.read_bytes() for p in checkout.rglob("README.md")} == before


@pytest.mark.parametrize("target", ["docs/Archive/ADR/GUIDANCE.md", "docs/Archive/PREVIOUS_TASK_LOG.md"])
def test_named_archive_navigation_checks_existence_without_reading_history(checkout, monkeypatch, target):
    (checkout / "AGENTS.md").write_text(f"[Explicit history exception]({target})\n")
    read_text = Path.read_text
    def guarded_read(path, *args, **kwargs):
        if "Archive" in path.parts:
            pytest.fail("routine document checking read historical content")
        return read_text(path, *args, **kwargs)
    monkeypatch.setattr(Path, "read_text", guarded_read)
    check_documents(checkout)
    (checkout / target).unlink()
    with pytest.raises(ValueError, match="missing repository reference"):
        check_documents(checkout)


@pytest.mark.parametrize("entries", [0, 1, 2, 3])
def test_rolling_task_log_rejects_a_third_completed_entry(checkout, entries):
    path = checkout / "docs/TASK_LOG.md"
    path.write_text("# Task Log\n\n" + "".join(
        f"## Completed task {index}\n\nResult: verified.\n\n" for index in range(entries)))
    result = run(checkout)
    assert result.returncode == (1 if entries > 2 else 0)
    if entries > 2:
        assert "TASK_LOG retains at most two completed entries" in result.stderr


@pytest.mark.parametrize("source", ["from ..science.admission import admit_scientific_evidence",
                                   "from src.science import admission",
                                   "import science.admission",
                                   "import upstream.client as old"])
def test_guarded_imports_reject_direct_bypasses_without_matching_prose(checkout, source):
    path = checkout / "src/director/tools.py"
    path.parent.mkdir()
    path.write_text('"""science.admission and upstream are documentation here."""\n')
    check_imports(checkout)
    path.write_text(source + "\n")
    with pytest.raises(ValueError):
        check_imports(checkout)
