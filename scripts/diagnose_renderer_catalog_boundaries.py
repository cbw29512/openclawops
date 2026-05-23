from __future__ import annotations

import ast
import logging
from pathlib import Path


# State schema:
# ROOT: local project root.
# LEGACY_PATH: current working factory module after report/audit extractions.
# FUNCTION_KEYWORDS: names likely tied to HTML rendering.
# ASSIGNMENT_KEYWORDS: top-level constants likely tied to renderer catalogs/config.
ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
LEGACY_PATH = ROOT / "scripts" / "nothingbuta_factory" / "legacy_factory.py"

FUNCTION_KEYWORDS = ("render", "html", "template")
ASSIGNMENT_KEYWORDS = ("renderer", "renderers", "catalog", "config", "template", "tool")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def read_source(path: Path) -> str:
    """Read the legacy factory safely so this diagnostic stays read-only."""
    try:
        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path}")

        return path.read_text(encoding="utf-8")
    except Exception as exc:
        logging.exception("Failed reading source.")
        raise SystemExit(1) from exc


def parse_source(source: str) -> ast.Module:
    """Parse Python source so line boundaries are accurate."""
    try:
        return ast.parse(source)
    except SyntaxError as exc:
        logging.exception("Legacy factory does not parse.")
        raise SystemExit(1) from exc


def assignment_name(node: ast.AST) -> str | None:
    """Return a readable name for simple top-level assignments."""
    try:
        if isinstance(node, ast.Assign):
            first_target = node.targets[0]
            if isinstance(first_target, ast.Name):
                return first_target.id

        if isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                return node.target.id

        return None
    except Exception:
        logging.exception("Failed reading assignment node.")
        return None


def main() -> None:
    """Print renderer/catalog boundary candidates without changing files."""
    source = read_source(LEGACY_PATH)
    tree = parse_source(source)
    lines = source.splitlines()

    print("=== Renderer Catalog Boundary Diagnostic ===")
    print(f"legacy_path: {LEGACY_PATH}")
    print(f"legacy_line_count: {len(lines)}")

    print("")
    print("=== Renderer-like functions ===")
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue

        lowered = node.name.lower()
        if any(keyword in lowered for keyword in FUNCTION_KEYWORDS):
            line_count = node.end_lineno - node.lineno + 1
            print(f"{node.name}: lines {node.lineno}-{node.end_lineno} ({line_count} lines)")

    print("")
    print("=== Catalog/config/template-like assignments ===")
    for node in tree.body:
        name = assignment_name(node)
        if not name:
            continue

        lowered = name.lower()
        if any(keyword in lowered for keyword in ASSIGNMENT_KEYWORDS):
            line_count = node.end_lineno - node.lineno + 1
            first_line = lines[node.lineno - 1].strip()
            print(f"{name}: lines {node.lineno}-{node.end_lineno} ({line_count} lines)")
            print(f"  first_line: {first_line}")


if __name__ == "__main__":
    main()