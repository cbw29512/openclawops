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
FREEZE_PATH = SCRIPTS / "nova_nothingbuta_release_freeze_packet.py"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def backup_file(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = path.with_name(f"{path.name}.bak-release-freeze-autopilot-{stamp}")
    shutil.copy2(path, backup_path)
    return backup_path


def compile_file(path: Path) -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        return False
    return True


def patch_autopilot() -> Path:
    if not AUTOPILOT_PATH.exists():
        logging.error("Missing autopilot script: %s", AUTOPILOT_PATH)
        raise SystemExit(1)

    if not FREEZE_PATH.exists():
        logging.error("Missing freeze packet script: %s", FREEZE_PATH)
        raise SystemExit(1)

    source = AUTOPILOT_PATH.read_text(encoding="utf-8")

    freeze_line = '    ["python", str(SCRIPTS / "nova_nothingbuta_release_freeze_packet.py")],'

    if freeze_line in source:
        print("Release freeze packet is already in safe autopilot.")
        return AUTOPILOT_PATH

    anchor = '    ["python", str(SCRIPTS / "nova_nothingbuta_release_batch_picker.py")],'

    if anchor not in source:
        logging.error("Could not find release picker command anchor in autopilot.")
        raise SystemExit(1)

    backup_path = backup_file(AUTOPILOT_PATH)
    patched = source.replace(anchor, anchor + "\n" + freeze_line, 1)
    AUTOPILOT_PATH.write_text(patched, encoding="utf-8")

    return backup_path


def run_autopilot_once() -> bool:
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


def main() -> None:
    backup_path = patch_autopilot()

    compile_ok = compile_file(AUTOPILOT_PATH)
    run_ok = run_autopilot_once() if compile_ok else False

    print("NOTHINGBUTA RELEASE FREEZE AUTOPILOT PATCH")
    print(f"backup: {backup_path}")
    print(f"compile_ok: {compile_ok}")
    print(f"run_ok: {run_ok}")

    if not compile_ok or not run_ok:
        logging.error("Patch validation failed. Roll back from backup before continuing.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()