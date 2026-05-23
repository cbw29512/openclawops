from __future__ import annotations

import ast
import logging
from pathlib import Path


# -----------------------------
# State schema:
# ROOT: local OpenClawOps root.
# LEGACY_PATH: current working factory file after report/audit extraction.
# TARGET_FUNCTIONS: renderer functions being considered for extraction.
# -----------------------------
ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
LEGACY_PATH = ROOT / "scripts" / "nothingbuta_factory" / "legacy_factory.py"
TARGET_FUNCTIONS = {"html_shell", "days_between_html"}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def read_source(path: Path) -> str:
    """Read the factory source without changing anything."""
    try:
        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path}")
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        logging.exception("Failed to read source.")
        raise SystemExit(1) from exc


def parse_source(source: str) -> ast.Module:
    """Parse source so function boundaries and symbol use are reliable."""
    try:
        return ast.parse(source)
    except SyntaxError as exc:
        logging.exception("Factory source does not parse.")
        raise SystemExit(1) from exc


def collect_top_level_symbols(tree: ast.Module) -> set[str]:
    """Collect top-level names that renderer functions may reference."""
    symbols: set[str] = set()

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            symbols.add(node.name)

        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    symbols.add(target.id)

        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            symbols.add(node.target.id)

    return symbols


def collect_loaded_names(function_node: ast.FunctionDef) -> set[str]:
    """Collect loaded variable names inside a function."""
    names: set[str] = set()

    for node in ast.walk(function_node):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            names.add(node.id)

    return names


def collect_calls(function_node: ast.FunctionDef) -> set[str]:
    """Collect direct call names and method names inside a function."""
    calls: set[str] = set()

    for node in ast.walk(function_node):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)

    return calls


def main() -> None:
    """Print renderer dependency information only."""
    source = read_source(LEGACY_PATH)
    tree = parse_source(source)
    top_symbols = collect_top_level_symbols(tree)

    print("=== Renderer Dependency Diagnostic ===")
    print(f"legacy_path: {LEGACY_PATH}")

    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue

        if node.name not in TARGET_FUNCTIONS:
            continue

        loaded_names = collect_loaded_names(node)
        calls = collect_calls(node)
        candidate_globals = sorted(name for name in loaded_names if name in top_symbols)

        print("")
        print(f"## {node.name}")
        print(f"lines: {node.lineno}-{node.end_lineno}")
        print(f"line_count: {node.end_lineno - node.lineno + 1}")

        print("")
        print("referenced_top_level_symbols:")
        for name in candidate_globals:
            print(f"- {name}")

        print("")
        print("calls:")
        for name in sorted(calls):
            print(f"- {name}")


if __name__ == "__main__":
    main()