from __future__ import annotations

import ast
import logging
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# -----------------------------
# State schema:
# ROOT: local OpenClawOps root.
# LEGACY_PATH: current working factory after report/audit extractions.
# CATALOG_PATH: extracted renderer/tool catalog module.
# TARGET_NAME: exact top-level assignment being moved.
# -----------------------------
ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
SCRIPTS_DIR = ROOT / "scripts"
MODULE_DIR = SCRIPTS_DIR / "nothingbuta_factory"

LEGACY_PATH = MODULE_DIR / "legacy_factory.py"
CATALOG_PATH = MODULE_DIR / "renderer_catalog_v2.py"
ENTRYPOINT_PATH = SCRIPTS_DIR / "nova_nothingbuta_local_factory_loop.py"
REPORTS_PATH = MODULE_DIR / "reports_v2.py"
AUDIT_PATH = MODULE_DIR / "audit_rules_v2.py"
TARGET_NAME = "TOOL_CONFIGS"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def read_text(path: Path) -> str:
    """Read source text and fail clearly if the file is unavailable."""
    try:
        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path}")
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        logging.exception("Read failed: %s", path)
        raise SystemExit(1) from exc


def write_text(path: Path, text: str) -> None:
    """Write source text with explicit UTF-8 encoding."""
    try:
        path.write_text(text, encoding="utf-8")
    except Exception as exc:
        logging.exception("Write failed: %s", path)
        raise SystemExit(1) from exc


def backup_file(path: Path, label: str) -> Path:
    """Create a timestamped backup before changing a file."""
    try:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = path.with_name(f"{path.name}.bak-{label}-{stamp}")
        shutil.copy2(path, backup_path)
        return backup_path
    except Exception as exc:
        logging.exception("Backup failed: %s", path)
        raise SystemExit(1) from exc


def find_assignment(tree: ast.Module, name: str) -> ast.AST:
    """Find the exact top-level assignment node for TOOL_CONFIGS."""
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name:
                return node

        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return node

    logging.error("Could not find assignment: %s", name)
    raise SystemExit(1)


def compile_file(path: Path) -> bool:
    """Compile one Python file and return True only if it passes."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logging.error("Compile failed for %s\n%s\n%s", path, result.stdout, result.stderr)
            return False

        return True
    except Exception as exc:
        logging.exception("Compile check crashed: %s", path)
        raise SystemExit(1) from exc


def unit_test_catalog() -> bool:
    """Import the extracted catalog and verify it is usable."""
    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from nothingbuta_factory.renderer_catalog_v2 import TOOL_CONFIGS

        return isinstance(TOOL_CONFIGS, dict) and len(TOOL_CONFIGS) > 0
    except Exception:
        logging.exception("Catalog unit test failed.")
        return False


def main() -> None:
    """Install the renderer catalog extraction as one reversible patch."""
    source = read_text(LEGACY_PATH)

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        logging.exception("Legacy factory does not parse before extraction.")
        raise SystemExit(1) from exc

    assignment_node = find_assignment(tree, TARGET_NAME)

    if assignment_node.end_lineno is None:
        logging.error("AST did not provide an end line for %s.", TARGET_NAME)
        raise SystemExit(1)

    lines = source.splitlines()
    assignment_lines = lines[assignment_node.lineno - 1 : assignment_node.end_lineno]
    assignment_line_count = len(assignment_lines)

    if assignment_line_count < 100:
        logging.error("TOOL_CONFIGS assignment looks too small: %s lines. Stop.", assignment_line_count)
        raise SystemExit(1)

    legacy_backup = backup_file(LEGACY_PATH, "renderer-catalog-extract-v2")
    catalog_backup = backup_file(CATALOG_PATH, "pre-renderer-catalog-extract-v2") if CATALOG_PATH.exists() else None

    catalog_source = "\n".join(
        [
            "from __future__ import annotations",
            "",
            "from typing import Any",
            "",
            "",
            *assignment_lines,
            "",
        ]
    )

    write_text(CATALOG_PATH, catalog_source)

    replacement = [
        "from nothingbuta_factory.renderer_catalog_v2 import TOOL_CONFIGS",
    ]

    patched_lines = (
        lines[: assignment_node.lineno - 1]
        + replacement
        + lines[assignment_node.end_lineno :]
    )

    write_text(LEGACY_PATH, "\n".join(patched_lines) + "\n")

    compile_ok = all(
        [
            compile_file(CATALOG_PATH),
            compile_file(AUDIT_PATH),
            compile_file(REPORTS_PATH),
            compile_file(LEGACY_PATH),
            compile_file(ENTRYPOINT_PATH),
        ]
    )

    unit_ok = unit_test_catalog()

    print("")
    print("=== Renderer Catalog Extract V2 Result ===")
    print(f"legacy_backup: {legacy_backup}")
    print(f"catalog_backup: {catalog_backup}")
    print(f"catalog_path: {CATALOG_PATH}")
    print(f"tool_configs_lines_moved: {assignment_line_count}")
    print(f"compile_ok: {compile_ok}")
    print(f"temp_unit_test_ok: {unit_ok}")

    if not compile_ok or not unit_ok:
        logging.error("Validation failed. Roll back before continuing.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()