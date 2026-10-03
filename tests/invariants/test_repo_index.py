"""Public CLI contract for read-only static repository queries."""
from pathlib import Path
import json
import os
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "repo_index.py"


def query(root, *arguments):
    return subprocess.run([sys.executable, "-B", str(SCRIPT), "--root", str(root), *arguments],
                          capture_output=True, text=True, check=False)


def write(root, path, content):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


SOURCE = '''from pydantic import BaseModel as Base
from dataclasses import dataclass as data
from enum import StrEnum as TextEnum
from .base import Parent as Ancestor
raise RuntimeError("indexed code must never execute")

class Child(Ancestor):
    own: int = 7
    async def run(self, value: str = "x") -> str:
        def nested():
            import math as arithmetic
        return value

class Mode(TextEnum):
    ACTIVE = "active"
    STOPPED: str = "stopped"

@data(frozen=True)
class Packet:
    count: int

class Ordinary:
    pass
'''


def prepare(root):
    write(root, "src/base.py", "from pydantic import BaseModel as B\nclass Parent(B):\n    inherited: str\n")
    write(root, "src/sample.py", SOURCE)
    write(root, "src/__init__.py", "from .sample import Packet\n")


def test_cli_recognizes_declarations_without_executing_sources(tmp_path):
    prepare(tmp_path)
    result = query(tmp_path)
    assert result.returncode == 0, result.stderr
    records = json.loads(result.stdout)["records"]
    by_name = {r["qualified_name"]: r for r in records if r["kind"] != "import"}
    assert by_name["src.sample.Child"]["kind"] == "model"
    assert by_name["src.sample.Child"]["resolved_bases"] == ["src.base.Parent"]
    assert by_name["src.sample.Packet"]["model_style"] == "dataclass"
    assert by_name["src.sample.Ordinary"]["kind"] == "class"
    assert by_name["src.sample.Mode"]["kind"] == "enum"
    assert by_name["src.sample.Mode.ACTIVE"]["value"] == "'active'"
    assert by_name["src.sample.Mode.STOPPED"]["kind"] == "enum_member"
    assert by_name["src.sample.Child.own"]["annotation"] == "int"
    assert by_name["src.base.Parent.inherited"]["declared_on"] == "src.base.Parent"
    assert "src.sample.Child.inherited" not in by_name  # declaration owner, not runtime expansion
    assert by_name["src.sample.Child.run"]["asynchronous"] is True
    assert by_name["src.sample.Child.run.nested"]["kind"] == "function"
    imports = {r["qualified_name"]: r for r in records if r["kind"] == "import"}
    assert imports["src.sample.Ancestor"]["target"] == "src.base.Parent"
    assert imports["src.sample.Ancestor"]["level"] == 1
    assert imports["src.Packet"]["target"] == "src.sample.Packet"
    assert imports["src.sample.Child.run.nested.arithmetic"]["target"] == "math"
    assert (tmp_path / "src/sample.py").read_text(encoding="utf-8") == SOURCE


def test_cli_combines_filters_and_returns_honest_empty_results(tmp_path):
    prepare(tmp_path)
    write(tmp_path, "tests/other.py", "def run(): pass\n")
    result = query(tmp_path, "--kind", "function", "--kind", "field", "--name", "Child",
                   "--module", "src.sample", "--path", "src/sample.py")
    assert result.returncode == 0, result.stderr
    records = json.loads(result.stdout)["records"]
    assert {r["qualified_name"] for r in records} == {
        "src.sample.Child.own", "src.sample.Child.run", "src.sample.Child.run.nested"}
    empty = query(tmp_path, "--kind", "model", "--name", "Missing")
    assert empty.returncode == 0
    assert json.loads(empty.stdout)["records"] == []


def test_cli_is_root_independent_deterministic_and_excludes_vendor_trees(tmp_path):
    left, right = tmp_path / "left", tmp_path / "right"
    for root in (left, right):
        prepare(root)
        write(root, ".upstream/must_not_read.py", "invalid python @@@")
        write(root, "src/vendor/must_not_read.py", "invalid python @@@")
        write(root, "src/.upstream/must_not_read.py", "invalid python @@@")
        write(root, "src/__pycache__/must_not_read.py", "invalid python @@@")
        write(root, "web/ignored.py", "invalid python @@@")
    first, second = query(left), query(right)
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout == query(left).stdout
    assert [f["path"] for f in json.loads(first.stdout)["files"]] == [
        "src/__init__.py", "src/base.py", "src/sample.py"]


def test_cli_does_not_follow_linked_inputs_outside_its_scope(tmp_path):
    root = tmp_path / "workspace"
    prepare(root)
    outside = tmp_path / "outside"
    write(outside, "broken.py", "invalid python @@@")
    try:
        os.symlink(outside, root / "src/linked", target_is_directory=True)
        os.symlink(outside / "broken.py", root / "src/linked_file.py")
    except OSError as error:
        pytest.skip(f"host cannot create symbolic links: {error}")
    result = query(root)
    assert result.returncode == 0, result.stderr
    assert [f["path"] for f in json.loads(result.stdout)["files"]] == [
        "src/__init__.py", "src/base.py", "src/sample.py"]


@pytest.mark.parametrize("failure", ["syntax", "missing_root"])
def test_cli_never_returns_partial_inventory_on_failure(tmp_path, failure):
    root = tmp_path / "workspace"
    if failure == "syntax":
        prepare(root)
        write(root, "scripts/broken.py", "def broken(\n")
    result = query(root)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "unable to complete inventory" in result.stderr
    if failure == "syntax":
        assert "scripts/broken.py:1:" in result.stderr
