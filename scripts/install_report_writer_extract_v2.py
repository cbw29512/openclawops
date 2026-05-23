from __future__ import annotations

import ast
import json
import logging
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


# -----------------------------
# State schema:
# ROOT: project root.
# LEGACY_PATH: preserved working factory that currently owns write_run_reports.
# REPORTS_PATH: new extracted module.
# TARGET_FUNCTION: exact function being extracted.
# -----------------------------
ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
SCRIPTS_DIR = ROOT / "scripts"
MODULE_DIR = SCRIPTS_DIR / "nothingbuta_factory"
LEGACY_PATH = MODULE_DIR / "legacy_factory.py"
REPORTS_PATH = MODULE_DIR / "reports_v2.py"
ENTRYPOINT_PATH = SCRIPTS_DIR / "nova_nothingbuta_local_factory_loop.py"
TARGET_FUNCTION = "write_run_reports"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def read_text(path: Path) -> str:
    """Read UTF-8 source text and fail loudly if the file is missing."""
    try:
        if not path.exists():
            raise FileNotFoundError(f"Missing required file: {path}")
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        logging.exception("Read failed: %s", path)
        raise SystemExit(1) from exc


def write_text(path: Path, text: str) -> None:
    """Write UTF-8 text using one clear helper for easier failure logging."""
    try:
        path.write_text(text, encoding="utf-8")
    except Exception as exc:
        logging.exception("Write failed: %s", path)
        raise SystemExit(1) from exc


def find_function(source: str, name: str) -> ast.FunctionDef:
    """Find the target top-level function using AST instead of fragile string guessing."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        logging.exception("Cannot parse legacy factory.")
        raise SystemExit(1) from exc

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node

    logging.error("Target function not found: %s", name)
    raise SystemExit(1)


def backup_file(path: Path, label: str) -> Path:
    """Create a timestamped backup before any mutation."""
    try:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = path.with_name(f"{path.name}.bak-{label}-{stamp}")
        shutil.copy2(path, backup_path)
        return backup_path
    except Exception as exc:
        logging.exception("Backup failed: %s", path)
        raise SystemExit(1) from exc


def build_reports_module(function_lines: list[str]) -> str:
    """Build reports_v2.py with injected paths/helpers to avoid circular imports."""
    body_lines = function_lines[1:]

    converted: list[str] = []
    for line in body_lines:
        line = line.replace("RUNS_DIR", "runs_dir")
        line = line.replace("LATEST_JSON_PATH", "latest_json_path")
        line = line.replace("LATEST_REPORT_PATH", "latest_report_path")
        converted.append("        " + line if line.strip() else "")

    module_lines = [
        "from __future__ import annotations",
        "",
        "import logging",
        "from pathlib import Path",
        "from typing import Any, Callable",
        "",
        "logger = logging.getLogger(__name__)",
        "",
        "",
        "def write_run_reports_v2(",
        "    run: dict[str, Any],",
        "    runs_dir: Path,",
        "    latest_json_path: Path,",
        "    latest_report_path: Path,",
        "    write_json: Callable[[Path, Any], None],",
        "    write_text: Callable[[Path, str], None],",
        ") -> None:",
        "    \"\"\"Write per-run and latest factory reports using injected dependencies.\"\"\"",
        "    try:",
        *converted,
        "    except Exception:",
        "        logger.exception('Failed to write NothingButA factory reports.')",
        "        raise",
        "",
    ]

    return "\n".join(module_lines)


def build_legacy_wrapper() -> list[str]:
    """Keep the old public function name but delegate the real work."""
    return [
        "def write_run_reports(run: dict[str, Any]) -> None:",
        "    \"\"\"Delegate report writing to the extracted reports_v2 module.\"\"\"",
        "    from nothingbuta_factory.reports_v2 import write_run_reports_v2",
        "",
        "    return write_run_reports_v2(",
        "        run=run,",
        "        runs_dir=RUNS_DIR,",
        "        latest_json_path=LATEST_JSON_PATH,",
        "        latest_report_path=LATEST_REPORT_PATH,",
        "        write_json=write_json,",
        "        write_text=write_text,",
        "    )",
    ]


def compile_file(path: Path) -> bool:
    """Compile one Python file and print compiler output if it fails."""
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


def temp_unit_test_reports_module() -> bool:
    """Test the extracted writer in a temp folder so real latest reports are untouched."""
    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from nothingbuta_factory.reports_v2 import write_run_reports_v2

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            runs_dir = temp_path / "runs"
            runs_dir.mkdir(parents=True, exist_ok=True)

            latest_json_path = temp_path / "latest.json"
            latest_report_path = temp_path / "latest.md"

            def temp_write_json(path: Path, payload: dict[str, Any]) -> None:
                path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            def temp_write_text(path: Path, payload: str) -> None:
                path.write_text(payload, encoding="utf-8")

            fake_run = {
                "run_id": "unit-test-report-writer",
                "created_at": "2099-01-01T00:00:00-04:00",
                "status": "pass",
                "batch_size": 1,
                "backlog_candidate_count": 1,
                "weak_existing_marked": 0,
                "built_candidates": [
                    {
                        "name": "Unit Test Calculator",
                        "state": "local_preview_ready",
                        "strict_quality_score": 100,
                        "local_preview_path": "temp-preview.html",
                        "audit_problems": [],
                    }
                ],
            }

            write_run_reports_v2(
                run=fake_run,
                runs_dir=runs_dir,
                latest_json_path=latest_json_path,
                latest_report_path=latest_report_path,
                write_json=temp_write_json,
                write_text=temp_write_text,
            )

            return (
                (runs_dir / "unit-test-report-writer.json").exists()
                and (runs_dir / "unit-test-report-writer.md").exists()
                and latest_json_path.exists()
                and latest_report_path.exists()
            )
    except Exception as exc:
        logging.exception("Temp unit test failed.")
        return False


def main() -> None:
    """Install the report-writer extraction as one reversible patch."""
    source = read_text(LEGACY_PATH)
    node = find_function(source, TARGET_FUNCTION)
    lines = source.splitlines()

    function_lines = lines[node.lineno - 1 : node.end_lineno]
    if len(function_lines) != 64:
        logging.error("Expected 64-line function, found %s. Stop.", len(function_lines))
        raise SystemExit(1)

    legacy_backup = backup_file(LEGACY_PATH, "report-writer-extract-v2")
    reports_backup = backup_file(REPORTS_PATH, "pre-report-writer-extract-v2") if REPORTS_PATH.exists() else None

    reports_module = build_reports_module(function_lines)
    wrapper_lines = build_legacy_wrapper()

    patched_lines = lines[: node.lineno - 1] + wrapper_lines + lines[node.end_lineno :]
    write_text(REPORTS_PATH, reports_module)
    write_text(LEGACY_PATH, "\n".join(patched_lines) + "\n")

    compile_ok = all(
        [
            compile_file(REPORTS_PATH),
            compile_file(LEGACY_PATH),
            compile_file(ENTRYPOINT_PATH),
        ]
    )
    unit_ok = temp_unit_test_reports_module()

    print("")
    print("=== Report Writer Extract V2 Result ===")
    print(f"legacy_backup: {legacy_backup}")
    print(f"reports_backup: {reports_backup}")
    print(f"reports_path: {REPORTS_PATH}")
    print(f"compile_ok: {compile_ok}")
    print(f"temp_unit_test_ok: {unit_ok}")

    if not compile_ok or not unit_ok:
        logging.error("Patch installed but validation failed. Roll back before continuing.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()