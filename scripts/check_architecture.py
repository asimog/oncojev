"""Fast static integrity checks; semantic/native proof stays with its owning tests."""
from __future__ import annotations

import argparse
import ast
import hashlib
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

import yaml

if __package__:
    from .repo_index import Declarations, module_name, python_files
else:
    from repo_index import Declarations, module_name, python_files

ROOT = Path(__file__).resolve().parents[1]
CURRENT_DOCS = ("README.md", "AGENTS.md", "docs/ARCHITECTURE.md",
                "docs/IMPLEMENTATION_PLAN.md", "docs/TASK_LOG.md",
                "docs/CAPABILITIES.md", "docs/JEV.md", "docs/FRONTEND.md")
CANONICAL = {"docs/ARCHITECTURE.md", "AGENTS.md"}
CLASSES = {"ENFORCED", "TESTED", "REVIEWED"}


def owned_path(root: Path, name: str) -> Path:
    """Resolve references without reading excluded or external input."""
    relative = Path(name)
    if relative.is_absolute() or "\\" in name or ".." in relative.parts:
        raise ValueError(f"invalid repository reference: {name}")
    if ".upstream" in relative.parts or relative.parts[:2] == ("docs", "Archive"):
        raise ValueError(f"excluded repository reference: {name}")
    path = root / relative
    for part in (root, *(root / Path(*relative.parts[:i]) for i in range(1, len(relative.parts) + 1))):
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise ValueError(f"linked repository reference: {name}")
    if not path.resolve().is_relative_to(root) or not path.exists():
        raise ValueError(f"missing repository reference: {name}")
    return path


def declarations(path: Path, root: Path) -> list[dict]:
    relative = path.relative_to(root)
    visitor = Declarations(relative.as_posix(), module_name(relative))
    visitor.visit(ast.parse(path.read_text(encoding="utf-8"), filename=str(relative)))
    return visitor.records


def check_projection(root: Path) -> None:
    projection = yaml.safe_load((root / "architecture.yaml").read_text(encoding="utf-8"))
    if projection.get("schema_version") != 1 or projection.get("authority") != "projection":
        raise ValueError("architecture.yaml must remain a version-1 projection")
    sources = projection["canonical_sources"]
    if len(sources) != len(CANONICAL) or {item["path"] for item in sources} != CANONICAL:
        raise ValueError("projection canonical sources must be Architecture and AGENTS")
    for item in sources:
        source = owned_path(root, item["path"])
        digest = hashlib.sha256(source.read_text(encoding="utf-8").encode()).hexdigest()
        if item["sha256"] != digest:
            raise ValueError(f"stale architecture projection: {item['path']} (review before refreshing hash)")
    if set(projection["classification"]) != CLASSES:
        raise ValueError("projection must retain ENFORCED, TESTED and REVIEWED")
    owners = projection["owners"]
    if not owners:
        raise ValueError("projection has no owners")
    for owner in owners.values():
        if not owner["paths"] or not owner["responsibility"] or not owner["forbidden"]:
            raise ValueError("each owner needs paths, responsibility and forbidden responsibilities")
        for name in owner["paths"]:
            owned_path(root, name)
    for section in ("authority_boundaries", "high_consequence_invariants"):
        if not projection[section]:
            raise ValueError(f"empty projection section: {section}")
        for claim in projection[section]:
            if claim["owner"] not in owners or claim["classification"] not in CLASSES:
                raise ValueError(f"unknown owner/classification: {claim}")
            if not claim["statement"] or not claim["evidence"]:
                raise ValueError("projection claim needs a statement and evidence")
            for reference in claim["evidence"]:
                name, separator, symbol = reference.partition("::")
                path = owned_path(root, name)
                if not path.is_file():
                    raise ValueError(f"evidence must name a file: {reference}")
                matches = []
                if separator:
                    if path.suffix != ".py":
                        raise ValueError(f"symbol evidence must be Python: {reference}")
                    qualified = f"{module_name(path.relative_to(root))}.{symbol}"
                    matches = [record for record in declarations(path, root)
                               if record["qualified_name"] == qualified and record["kind"] != "import"]
                    if not matches:
                        raise ValueError(f"missing evidence symbol: {reference}")
                if claim["classification"] == "TESTED" and not (
                    name.startswith("tests/") and matches and
                    any(record["kind"] == "function" and record["name"].startswith("test_")
                        for record in matches)
                ):
                    raise ValueError(f"TESTED evidence must name a test function: {reference}")
    # Authority/data-flow endpoints only; no import-layer or cycle constraint.
    for direction in projection.get("dependency_directions", []):
        targets = direction["to"] if isinstance(direction["to"], list) else [direction["to"]]
        if any(owner not in owners for owner in [direction["from"], *targets]):
            raise ValueError(f"unknown data-flow owner: {direction}")


def prose(text: str) -> str:
    return re.sub(r"(?ms)^\s*(`{3,}|~{3,})[^\n]*\n.*?^\s*\1\s*$", "", text)


def check_documents(root: Path) -> None:
    # Explicit active surface only; no historical document/source-input scan.
    documents = [owned_path(root, name) for name in CURRENT_DOCS]
    source = root / "src"
    documents += sorted(source.glob("*/README.md"))
    documents += sorted((source / "oncolab" / "labskills").glob("README.md"))
    for document in documents:
        document = owned_path(root, document.relative_to(root).as_posix())
        text = prose(document.read_text(encoding="utf-8"))
        relative = document.relative_to(root).as_posix()
        if relative != "docs/IMPLEMENTATION_PLAN.md" and re.search(
            r"(?im)^#{1,6}\s+(?:Task\s+\d+\b|(?:Roadmap|Backlog|Future work)\s*$)|^\s*[-*]\s+\[ \]", text
        ):
            raise ValueError(f"planning structure outside implementation plan: {relative}")
        if relative == "docs/TASK_LOG.md" and re.search(
            r"(?im)^\s*(?:\*\*)?(?:Done when|Depends on|Dependencies|Priority)\s*:|"
            r"^\s*(?:\*\*)?Status\s*:\s*(?:pending|planned|blocked|in.progress|active)\b", text
        ):
            raise ValueError("TASK_LOG contains active planning fields")
        for target in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", text):
            target = target.strip().strip("<>")
            url = urlsplit(target)
            if url.scheme or url.netloc:
                continue
            name = (document.parent / unquote(url.path)).resolve() if url.path else document
            if not name.is_relative_to(root):
                raise ValueError(f"external local link in {relative}: {target}")
            linked = owned_path(root, name.relative_to(root).as_posix())
            if url.fragment and linked.suffix == ".md":
                headings = re.findall(r"(?m)^#{1,6}\s+(.+)$", prose(linked.read_text(encoding="utf-8")))
                anchors = {re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-") for heading in headings}
                if unquote(url.fragment) not in anchors:
                    raise ValueError(f"missing heading link in {relative}: {target}")


def check_imports(root: Path) -> None:
    guarded = {"director", "persistence", "application", "api", "memory"}
    for path in python_files(root):
        relative = path.relative_to(root)
        if relative.parts[0] != "src":
            continue
        for record in declarations(path, root):
            if record["kind"] != "import":
                continue
            target = record["target"]
            if "upstream" in target.split("."):
                raise ValueError(f"runtime imports upstream: {relative}")
            if len(relative.parts) > 1 and relative.parts[1] in guarded and (
                target in {"src.science.admission", "science.admission"}
                or target.startswith(("src.science.admission.", "science.admission."))
                or target.endswith(".admit_scientific_evidence")
            ):
                raise ValueError(f"owner must not import evidence admission: {relative}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs-only", action="store_true", help="projection/document integrity without application imports")
    parser.add_argument("--root", type=Path, default=ROOT, help="alternate checkout (docs-only)")
    args = parser.parse_args()
    root = args.root.resolve()
    if root != ROOT and not args.docs_only:
        parser.error("alternate --root requires --docs-only")
    try:
        check_projection(root)
        check_documents(root)
        if not args.docs_only:
            check_imports(root)
            owned_path(root, "src/oncolab/README.md")
            if (root / "registries").exists():
                raise ValueError("capability records must live under src/oncolab, not registries/")
            from src.oncolab.catalogue import initial_oncolab_index
            index = initial_oncolab_index()
            for kind in index.list_kinds():
                for descriptor in index.search(kinds=(kind,), limit=20):
                    for record in index.verification_records(descriptor.capability_id):
                        if record.execution_reference.kind != "file":
                            raise ValueError("bundled verification must be portable")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, SyntaxError, yaml.YAMLError) as error:
        print(f"architecture check failed: {error}", file=sys.stderr)
        raise SystemExit(1)
    print("architecture checks passed" + (" (documents/projection only)" if args.docs_only else ""))


if __name__ == "__main__":
    main()
