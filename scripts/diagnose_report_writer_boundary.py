from __future__ import annotations

import ast
import logging
import subprocess
import sys
from pathlib import Path


# -----------------------------
# State schema:
# This script is read-only. It only inspects the legacy factory file.
# -----------------------------
ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
LEGACY_PATH = ROOT / "scripts" / "nothingbuta_factory" / "legacy_factory.py"
TARGET_FUNCTION = "write_run_reports"

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)


def read_source(path: Path) -> str:
    """Read source text with clear failure logging."""
    try:
        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path}")

        return path.read_text(encoding="utf-8")
    except Exception as exc:
        logging.exception("Failed reading source file.")
        raise SystemExit(1) from exc


def find_function_span(source: str, function_name: str) -> ast.FunctionDef:
    """Use Python AST so we do not guess line numbers by text matching."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        logging.exception("Legacy factory has a syntax error; stop before extraction.")
        raise SystemExit(1) from exc

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return node

    logging.error("Could not find function: %s", function_name)
    raise SystemExit(1)


def collect_imports(source: str) -> list[str]:
    """Collect top-level imports that may be needed by the extracted module."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        logging.exception("Could not parse imports.")
        raise SystemExit(1) from exc

    imports: list[str] = []

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            line = source.splitlines()[node.lineno - 1]
            imports.append(line)

    return imports


def collect_function_calls(function_node: ast.FunctionDef) -> list[str]:
    """List called function names inside the target function."""
    calls: set[str] = set()

    for node in ast.walk(function_node):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)

    return sorted(calls)


def compile_check(path: Path) -> bool:
    """Compile-check the legacy file after inspection."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logging.error("Compile failed:\n%s\n%s", result.stdout, result.stderr)
            return False

        return True
    except Exception as exc:
        logging.exception("Compile check crashed.")
        raise SystemExit(1) from exc


def main() -> None:
    """Run the read-only diagnostic."""
    source = read_source(LEGACY_PATH)
    lines = source.splitlines()

    function_node = find_function_span(source, TARGET_FUNCTION)
    imports = collect_imports(source)
    calls = collect_function_calls(function_node)
    compiles = compile_check(LEGACY_PATH)

    print("")
    print("=== Report Writer Boundary Diagnostic ===")
    print(f"legacy_path: {LEGACY_PATH}")
    print(f"function_name: {TARGET_FUNCTION}")
    print(f"start_line: {function_node.lineno}")
    print(f"end_line: {function_node.end_lineno}")
    print(f"line_count: {function_node.end_lineno - function_node.lineno + 1}")
    print(f"factory_still_compiles: {compiles}")

    print("")
    print("=== Function Header ===")
    print(lines[function_node.lineno - 1])

    print("")
    print("=== Imports Found ===")
    for item in imports:
        print(item)

    print("")
    print("=== Calls Inside write_run_reports ===")
    for call in calls:
        print(call)


if __name__ == "__main__":
    main()