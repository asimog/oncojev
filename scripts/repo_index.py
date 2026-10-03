"""Read-only Python declaration queries; never imports indexed code. See AGENTS.md."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import sys
import tokenize

SCOPES = ("src", "scripts", "tests")
EXCLUDED = {".upstream", ".git", ".venv", "venv", "__pycache__", "node_modules", "vendor", "vendored"}
KINDS = ("module", "class", "model", "enum", "function", "field", "enum_member", "import")


def syntax(node: ast.AST | None) -> str | None:
    return ast.unparse(node) if node is not None else None


def linked(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def python_files(root: Path):
    for scope in SCOPES:
        start = root / scope
        if not start.is_dir() or linked(start):
            continue
        def walk_error(error):
            raise error
        for directory, dirs, files in os.walk(start, followlinks=False, onerror=walk_error):
            dirs[:] = sorted(d for d in dirs if d not in EXCLUDED and not linked(Path(directory) / d))
            for name in sorted(files):
                path = Path(directory) / name
                if name.endswith(".py") and not linked(path):
                    yield path


def module_name(relative: Path) -> str:
    parts = list(relative.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


class Declarations(ast.NodeVisitor):
    def __init__(self, path: str, module: str):
        self.path, self.module = path, module
        self.scope: list[str] = []
        self.records: list[dict] = []
        self.aliases: dict[str, str] = {}

    def add(self, kind: str, name: str, node: ast.AST, **metadata):
        qualified = ".".join([self.module, *self.scope, name])
        record = {"kind": kind, "name": name, "qualified_name": qualified,
                  "module": self.module, "path": self.path,
                  "line": node.lineno, "end_line": node.end_lineno, **metadata}
        self.records.append(record)
        return record

    def visit_ClassDef(self, node: ast.ClassDef):
        self.add("class", node.name, node, bases=[syntax(b) for b in node.bases],
                 decorators=[syntax(d) for d in node.decorator_list])
        self.scope.append(node.name)
        for statement in node.body:
            if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                self.add("field", statement.target.id, statement,
                         annotation=syntax(statement.annotation), default=syntax(statement.value))
            elif isinstance(statement, ast.Assign):
                for target in statement.targets:
                    if isinstance(target, ast.Name):
                        self.add("assignment", target.id, statement, value=syntax(statement.value))
            self.visit(statement)
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        self.add("function", node.name, node, asynchronous=isinstance(node, ast.AsyncFunctionDef),
                 arguments=syntax(node.args), returns=syntax(node.returns),
                 decorators=[syntax(d) for d in node.decorator_list])
        self.scope.append(node.name)
        for statement in node.body:
            self.visit(statement)
        self.scope.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            binding = alias.asname or alias.name.split(".")[0]
            self.add("import", binding, node, target=alias.name, binding=binding, level=0)
            if not self.scope:
                self.aliases[binding] = alias.name if alias.asname else binding

    def visit_ImportFrom(self, node: ast.ImportFrom):
        # A package __init__ and a normal module have different relative bases.
        package = self.module.split(".") if self.path.endswith("/__init__.py") else self.module.split(".")[:-1]
        prefix = package[:len(package) - node.level + 1] if node.level else []
        absolute = ".".join([*prefix, *([node.module] if node.module else [])])
        for alias in node.names:
            binding = alias.asname or alias.name
            target = ".".join(filter(None, [absolute, alias.name]))
            self.add("import", binding, node, target=target, binding=binding,
                     level=node.level, source_module=node.module)
            if not self.scope:
                self.aliases[binding] = target


def classify(records: list[dict], aliases: dict[str, dict[str, str]]):
    classes = {r["qualified_name"]: r for r in records if r["kind"] == "class"}

    def resolve(expression: str, record: dict) -> str:
        # Ignore generic parameters for inheritance recognition, retaining original syntax.
        expression = expression.split("[", 1)[0]
        head, *tail = expression.split(".")
        imports = aliases[record["path"]]
        if head in imports:
            return ".".join([imports[head], *tail])
        parent = record["qualified_name"].rsplit(".", 1)[0]
        while parent:
            candidate = f"{parent}.{expression}"
            if candidate in classes:
                return candidate
            parent = parent.rpartition(".")[0]
        return expression

    for record in classes.values():
        record["resolved_bases"] = [resolve(b, record) for b in record["bases"]]
        decorators = [resolve(d.split("(", 1)[0], record) for d in record["decorators"]]
        if "dataclasses.dataclass" in decorators:
            record["kind"] = "model"
            record["model_style"] = "dataclass"
    changed = True
    while changed:
        changed = False
        for record in classes.values():
            if record["kind"] != "class":
                continue
            for base in record["resolved_bases"]:
                ancestor = classes.get(base, {})
                if base in {"pydantic.BaseModel", "pydantic.main.BaseModel"} or ancestor.get("kind") == "model":
                    record.update(kind="model", model_style=ancestor.get("model_style", "pydantic"))
                    changed = True
                    break
                if base in {"enum.Enum", "enum.IntEnum", "enum.StrEnum", "enum.Flag", "enum.IntFlag"} or ancestor.get("kind") == "enum":
                    record["kind"] = "enum"
                    changed = True
                    break
    output = []
    for record in records:
        owner = classes.get(record["qualified_name"].rsplit(".", 1)[0])
        if record["kind"] == "assignment":
            if not owner or owner["kind"] != "enum" or record["name"].startswith("_"):
                continue
            record["kind"] = "enum_member"
        if record["kind"] == "field":
            record["declared_on"] = owner["qualified_name"]
            if owner["kind"] == "enum" and record["default"] is not None and not record["name"].startswith("_"):
                record["kind"] = "enum_member"
                record["value"] = record.pop("default")
        output.append(record)
    return output


def inventory(root: Path) -> dict:
    records, files, aliases = [], [], {}
    for path in sorted(python_files(root)):
        relative = path.relative_to(root)
        label = relative.as_posix()
        raw = path.read_bytes()
        with tokenize.open(path) as stream:
            tree = ast.parse(stream.read(), filename=label)
        module = module_name(relative)
        files.append({"path": label, "sha256": hashlib.sha256(raw).hexdigest()})
        records.append({"kind": "module", "name": module.rsplit(".", 1)[-1],
                        "qualified_name": module, "module": module, "path": label,
                        "line": 1, "end_line": max((getattr(n, "end_lineno", 1) or 1 for n in tree.body), default=1)})
        visitor = Declarations(label, module)
        visitor.visit(tree)
        records.extend(visitor.records)
        aliases[label] = visitor.aliases
    return {"schema_version": 1, "scope": list(SCOPES), "files": files,
            "records": sorted(classify(records, aliases), key=lambda r: (r["path"], r["line"], r["kind"], r["qualified_name"]))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--kind", choices=KINDS, action="append", help="Repeat to include several kinds")
    parser.add_argument("--name", default="", help="Qualified-name substring (case sensitive)")
    parser.add_argument("--module", default="", help="Module prefix")
    parser.add_argument("--path", default="", help="Repository-relative POSIX path prefix")
    args = parser.parse_args()
    try:
        root = args.root.resolve(strict=True)
        if not root.is_dir():
            raise ValueError("root must be a directory")
        result = inventory(root)
    except (OSError, SyntaxError, UnicodeError, ValueError) as error:
        # Avoid printing absolute workspace paths or any indexed source text.
        if isinstance(error, SyntaxError):
            detail = f"{error.filename}:{error.lineno}: {error.msg}"
        else:
            detail = type(error).__name__
        print(f"repo_index: unable to complete inventory: {detail}", file=sys.stderr)
        return 2
    result["query"] = {"kind": sorted(set(args.kind or [])), "name": args.name,
                       "module": args.module, "path": args.path}
    result["records"] = [r for r in result["records"]
                         if (not args.kind or r["kind"] in args.kind)
                         and args.name in r["qualified_name"]
                         and r["module"].startswith(args.module)
                         and r["path"].startswith(args.path)]
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
