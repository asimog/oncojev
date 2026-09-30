"""Cheap mechanical checks for enduring repository boundaries."""
from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"


def imports_forbidden_upstream(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == ".upstream" or alias.name.startswith(".upstream.") for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module == ".upstream" or node.module.startswith(".upstream."):
                return True
    return False


def main() -> None:
    runtime_files = tuple(SOURCE.rglob("*.py"))
    offenders = [path.relative_to(ROOT) for path in runtime_files if imports_forbidden_upstream(path)]
    if offenders:
        raise SystemExit(f"runtime imports .upstream: {offenders}")

    director = SOURCE / "director"
    if any("science.admission" in path.read_text(encoding="utf-8") for path in director.glob("*.py")):
        raise SystemExit("Director must not import Science admission.")

    for package in ("persistence", "application", "api"):
        for path in (SOURCE / package).rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "science.admission" in text or "admit_scientific_evidence" in text:
                raise SystemExit(f"{package} must not bypass evidence admission: {path}")

    web = ROOT / "web"
    if web.exists():
        forbidden = ("admit_scientific_evidence", "FrontierPolicy", "src.science", "src.runtime")
        for path in (*web.rglob("*.ts"), *web.rglob("*.tsx")):
            if "node_modules" in path.parts or ".next" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            if any(token in text for token in forbidden):
                raise SystemExit(f"frontend must stay presentation-only: {path.relative_to(ROOT)}")

    required = (
        ROOT / "src" / "oncolab" / "README.md",
        ROOT / ".upstream" / "manifest.yaml",
    )
    missing = [path.relative_to(ROOT) for path in required if not path.is_file()]
    if missing:
        raise SystemExit(f"missing architecture records: {missing}")
    if (ROOT / "registries").exists():
        raise SystemExit("capability records must live under src/oncolab, not registries/")
    print("architecture checks passed")


if __name__ == "__main__":
    main()
