from __future__ import annotations

import logging
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
SCRIPTS = ROOT / "scripts"

AUTOPILOT_PATH = SCRIPTS / "nova_nothingbuta_safe_autopilot_check.py"
OPTIMIZER_PATH = SCRIPTS / "nova_nothingbuta_hourly_optimizer_report.py"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def backup_file(path: Path) -> Path:
    try:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = path.with_name(f"{path.name}.bak-hourly-optimizer-autopilot-{stamp}")
        shutil.copy2(path, backup_path)
        return backup_path
    except Exception as exc:
        logging.exception("Backup failed.")
        raise SystemExit(1) from exc


def compile_file(path: Path) -> bool:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.stdout.strip():
            print(result.stdout)

        if result.stderr.strip():
            print(result.stderr)

        return result.returncode == 0
    except Exception as exc:
        logging.exception("Compile check crashed.")
        raise SystemExit(1) from exc


def patch_autopilot() -> Path:
    try:
        if not AUTOPILOT_PATH.exists():
            raise FileNotFoundError(f"Missing autopilot script: {AUTOPILOT_PATH}")

        if not OPTIMIZER_PATH.exists():
            raise FileNotFoundError(f"Missing optimizer script: {OPTIMIZER_PATH}")

        source = AUTOPILOT_PATH.read_text(encoding="utf-8")

        optimizer_block = '''    {
        "label": "hourly optimizer report",
        "command": ["python", str(SCRIPTS / "nova_nothingbuta_hourly_optimizer_report.py")],
    },'''

        if "nova_nothingbuta_hourly_optimizer_report.py" in source:
            print("Hourly optimizer is already in safe autopilot.")
            return AUTOPILOT_PATH

        anchor = '''    {
        "label": "staging copy dry run",
        "command": ["python", str(SCRIPTS / "nova_nothingbuta_local_staging_copy.py")],
    },'''

        if anchor not in source:
            raise ValueError("Could not find staging copy dry run command anchor in autopilot.")

        backup_path = backup_file(AUTOPILOT_PATH)
        patched = source.replace(anchor, anchor + "\n" + optimizer_block, 1)
        AUTOPILOT_PATH.write_text(patched, encoding="utf-8")

        return backup_path
    except Exception as exc:
        logging.exception("Failed to patch autopilot.")
        raise SystemExit(1) from exc


def run_autopilot_once() -> bool:
    try:
        result = subprocess.run(
            [sys.executable, str(AUTOPILOT_PATH)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

        print(result.stdout)

        if result.stderr.strip():
            print(result.stderr)

        return result.returncode == 0
    except Exception as exc:
        logging.exception("Autopilot proof run crashed.")
        raise SystemExit(1) from exc


def main() -> None:
    backup_path = patch_autopilot()

    compile_ok = compile_file(AUTOPILOT_PATH)
    run_ok = run_autopilot_once() if compile_ok else False

    print("NOTHINGBUTA HOURLY OPTIMIZER AUTOPILOT PATCH")
    print(f"backup: {backup_path}")
    print(f"compile_ok: {compile_ok}")
    print(f"run_ok: {run_ok}")

    if not compile_ok or not run_ok:
        logging.error("Patch validation failed. Roll back from backup before continuing.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()