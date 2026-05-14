from __future__ import annotations

import os
import re
from pathlib import Path
from collections import defaultdict

EXCLUDE_DIRS = {
    ".git",
    ".github",
    ".vscode",
    "node_modules",
    "dist",
    "build",
    "coverage",
    ".venv",
    "venv",
    "__pycache__",
    ".next",
    ".nuxt",
    ".idea",
    "scraped_recipes.jsonl",
}

PY_IMPORT_RE = re.compile(r"^\s*import\s+([a-zA-Z_][\w\.]*)", re.M)
PY_FROM_RE = re.compile(r"^\s*from\s+([a-zA-Z_][\w\.]*)\s+import\s+", re.M)

JS_IMPORT_RE = re.compile(r"^\s*import\s+.*?\s+from\s+['\"](.+?)['\"]\s*;?\s*$", re.M)
JS_REQUIRE_RE = re.compile(r"require\(\s*['\"](.+?)['\"]\s*\)")

CODE_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx"}


def is_excluded_dir(path: Path) -> bool:
    parts = set(path.parts)
    return any(p in EXCLUDE_DIRS for p in parts)


def top_level_package(repo_root: Path, file_path: Path) -> str | None:
    try:
        rel = file_path.relative_to(repo_root)
    except ValueError:
        return None
    if not rel.parts:
        return None
    top = rel.parts[0]
    if top.startswith(".") or top in EXCLUDE_DIRS:
        return None
    if (repo_root / top).is_dir():
        return top
    return None


def iter_code_files(repo_root: Path):
    for root, dirs, files in os.walk(repo_root):
        root_path = Path(root)
        # prune excluded dirs in-place
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
        if is_excluded_dir(root_path):
            continue
        for name in files:
            p = root_path / name
            if p.suffix in CODE_EXTS and not name.startswith("."):
                yield p


def extract_import_targets(text: str):
    targets = set()
    # Python
    targets |= set(PY_IMPORT_RE.findall(text))
    targets |= set(PY_FROM_RE.findall(text))
    # JS/TS
    targets |= set(JS_IMPORT_RE.findall(text))
    targets |= set(JS_REQUIRE_RE.findall(text))
    return targets


def resolve_relative_import(source_file: Path, spec: str) -> Path | None:
    # Only handle local relative JS/TS imports like "./x", "../y"
    if not (spec.startswith("./") or spec.startswith("../")):
        return None
    base = source_file.parent
    p = (base / spec).resolve()
    return p


def main():
    repo_root = Path(__file__).resolve().parents[1]

    packages = set()
    deps = defaultdict(set)  # pkg -> set[pkg]

    for f in iter_code_files(repo_root):
        src_pkg = top_level_package(repo_root, f)
        if not src_pkg:
            continue
        packages.add(src_pkg)

        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for spec in extract_import_targets(text):
            # JS/TS relative import resolution to a filesystem path -> package
            rel_path = resolve_relative_import(f, spec)
            if rel_path:
                # try common extensions / index files
                candidates = []
                if rel_path.suffix:
                    candidates.append(rel_path)
                else:
                    candidates += [
                        rel_path.with_suffix(ext)
                        for ext in [".ts", ".tsx", ".js", ".jsx"]
                    ]
                    candidates += [
                        rel_path / ("index" + ext)
                        for ext in [".ts", ".tsx", ".js", ".jsx"]
                    ]
                for c in candidates:
                    if c.exists():
                        tgt_pkg = top_level_package(repo_root, c)
                        if tgt_pkg and tgt_pkg != src_pkg:
                            packages.add(tgt_pkg)
                            deps[src_pkg].add(tgt_pkg)
                        break
                continue

            # Python absolute import: map first segment to top-level folder if it exists
            # e.g., "from api.utils import x" -> candidate "api"
            first = spec.split(".")[0].lstrip("@")
            if (repo_root / first).is_dir() and first not in EXCLUDE_DIRS:
                tgt_pkg = first
                if tgt_pkg != src_pkg:
                    packages.add(tgt_pkg)
                    deps[src_pkg].add(tgt_pkg)

    # Emit PlantUML
    lines = []
    lines.append("@startuml")
    lines.append("skinparam packageStyle rectangle")
    lines.append("hide empty members")
    lines.append("")

    for pkg in sorted(packages):
        lines.append(f'package "{pkg}" as {pkg} {{}}')

    lines.append("")
    for a in sorted(deps.keys()):
        for b in sorted(deps[a]):
            lines.append(f"{a} ..> {b}")

    lines.append("@enduml")

    out_dir = repo_root / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "packages.puml"
    out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote: {out_file}")


if __name__ == "__main__":
    main()
