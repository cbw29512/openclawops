from __future__ import annotations

import logging
import subprocess
from pathlib import Path


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
SCRIPTS = ROOT / "scripts"
REPORTS = ROOT / "reports"

TASK_NAME = "NothingButA Safe Autopilot Check"
RUNNER_PATH = SCRIPTS / "run_nothingbuta_safe_autopilot_check.ps1"
PYTHON_SCRIPT = SCRIPTS / "nova_nothingbuta_safe_autopilot_check.py"
LOG_PATH = REPORTS / "nothingbuta-safe-autopilot-check-task.log"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a command with captured output and clear error reporting."""
    try:
        result = subprocess.run(
            command,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

        if result.stdout.strip():
            print(result.stdout)

        if result.stderr.strip():
            print(result.stderr)

        return result
    except Exception as exc:
        logging.exception("Command crashed: %s", command)
        raise SystemExit(1) from exc


def write_runner() -> None:
    """Write the scheduled PowerShell runner."""
    try:
        REPORTS.mkdir(parents=True, exist_ok=True)

        runner = f'''$ErrorActionPreference = "Stop"

$Root = "{ROOT}"
$PythonScript = "{PYTHON_SCRIPT}"
$LogPath = "{LOG_PATH}"

Set-Location $Root

$Stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"[$Stamp] Starting NothingButA Safe Autopilot Check" | Out-File -FilePath $LogPath -Append -Encoding utf8

try {{
    python $PythonScript *>> $LogPath
    $ExitCode = $LASTEXITCODE

    $DoneStamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$DoneStamp] Finished with exit code $ExitCode" | Out-File -FilePath $LogPath -Append -Encoding utf8

    exit $ExitCode
}} catch {{
    $FailStamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$FailStamp] ERROR: $($_.Exception.Message)" | Out-File -FilePath $LogPath -Append -Encoding utf8
    exit 1
}}
'''
        RUNNER_PATH.write_text(runner, encoding="utf-8")
    except Exception as exc:
        logging.exception("Failed writing runner.")
        raise SystemExit(1) from exc


def register_task() -> None:
    """Register or replace the scheduled task."""
    task_action = (
        f'powershell.exe -NoProfile -ExecutionPolicy Bypass '
        f'-File "{RUNNER_PATH}"'
    )

    command = [
        "schtasks",
        "/Create",
        "/TN",
        TASK_NAME,
        "/SC",
        "MINUTE",
        "/MO",
        "30",
        "/TR",
        task_action,
        "/F",
    ]

    result = run_command(command)

    if result.returncode != 0:
        logging.error("Failed to register scheduled task.")
        raise SystemExit(1)


def run_task_once() -> None:
    """Start the scheduled task once for proof."""
    result = run_command(["schtasks", "/Run", "/TN", TASK_NAME])

    if result.returncode != 0:
        logging.error("Failed to start scheduled task.")
        raise SystemExit(1)


def query_task() -> None:
    """Print task status."""
    result = run_command(["schtasks", "/Query", "/TN", TASK_NAME, "/V", "/FO", "LIST"])

    if result.returncode != 0:
        logging.error("Failed to query scheduled task.")
        raise SystemExit(1)


def main() -> None:
    if not PYTHON_SCRIPT.exists():
        logging.error("Missing required script: %s", PYTHON_SCRIPT)
        raise SystemExit(1)

    write_runner()
    register_task()
    run_task_once()
    query_task()

    print("")
    print("NOTHINGBUTA SAFE AUTOPILOT TASK: INSTALLED")
    print(f"task_name: {TASK_NAME}")
    print(f"runner: {RUNNER_PATH}")
    print(f"log: {LOG_PATH}")
    print("schedule: every 30 minutes")
    print("safety: local-only, no publish/commit/push/outreach/ads/analytics/affiliate/lead capture")


if __name__ == "__main__":
    main()