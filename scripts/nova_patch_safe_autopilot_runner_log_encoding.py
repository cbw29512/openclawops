from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path


# Objective:
# Patch the NothingButA scheduled-task runner so logs are readable.
#
# This script DOES:
# - back up run_nothingbuta_safe_autopilot_check.ps1
# - replace the runner with a UTF-8-safe version
# - keep the same Python autopilot target
# - keep the same task log target
#
# This script DOES NOT:
# - change the scheduled task definition
# - change site files
# - commit
# - push
# - publish
# - add analytics, ads, affiliate links, lead capture, or outreach


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("patch_safe_autopilot_runner_log_encoding")


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
RUNNER_PATH = ROOT / "scripts" / "run_nothingbuta_safe_autopilot_check.ps1"


NEW_RUNNER = r'''$ErrorActionPreference = "Stop"

$Root = "C:\Users\dmchris\OpenClawOps"
$PythonScript = "C:\Users\dmchris\OpenClawOps\scripts\nova_nothingbuta_safe_autopilot_check.py"
$LogPath = "C:\Users\dmchris\OpenClawOps\reports\nothingbuta-safe-autopilot-check-task.log"

Set-Location $Root

# Force Python and PowerShell text output to UTF-8 so the task log stays readable.
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

function Write-TaskLog {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    $Message | Out-File -FilePath $LogPath -Append -Encoding utf8
}

$Stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-TaskLog "[$Stamp] Starting NothingButA Safe Autopilot Check"

try {
    # Capture Python stdout and stderr into PowerShell strings, then write them as UTF-8.
    # This avoids the spaced-out log issue caused by raw native redirection.
    & python $PythonScript 2>&1 | ForEach-Object {
        Write-TaskLog $_.ToString()
    }

    $ExitCode = $LASTEXITCODE

    $DoneStamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-TaskLog "[$DoneStamp] Finished with exit code $ExitCode"

    exit $ExitCode
}
catch {
    $FailStamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-TaskLog "[$FailStamp] ERROR: $($_.Exception.Message)"
    exit 1
}
'''


def main() -> int:
    try:
        if not RUNNER_PATH.exists():
            raise RuntimeError(f"Missing runner: {RUNNER_PATH}")

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = RUNNER_PATH.with_suffix(f".ps1.bak-log-encoding-{timestamp}")
        shutil.copy2(RUNNER_PATH, backup_path)

        RUNNER_PATH.write_text(NEW_RUNNER, encoding="utf-8")

        print("NOTHINGBUTA RUNNER LOG ENCODING PATCH: PASS")
        print("backup:", backup_path)
        print("runner:", RUNNER_PATH)
        return 0

    except Exception as exc:
        logger.exception("Runner patch failed")
        print("NOTHINGBUTA RUNNER LOG ENCODING PATCH: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
