from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path


# Objective:
# Fix the NothingButA scheduled-task runner so it accepts blank log lines.
#
# This script DOES:
# - back up run_nothingbuta_safe_autopilot_check.ps1
# - replace the runner with a UTF-8-safe version
# - allow empty stdout lines in Write-TaskLog
#
# This script DOES NOT:
# - change the scheduled task definition
# - change site files
# - commit
# - push
# - publish


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("patch_safe_autopilot_runner_allow_empty_log_lines")


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
RUNNER_PATH = ROOT / "scripts" / "run_nothingbuta_safe_autopilot_check.ps1"


NEW_RUNNER = r'''$ErrorActionPreference = "Stop"

$Root = "C:\Users\dmchris\OpenClawOps"
$PythonScript = "C:\Users\dmchris\OpenClawOps\scripts\nova_nothingbuta_safe_autopilot_check.py"
$LogPath = "C:\Users\dmchris\OpenClawOps\reports\nothingbuta-safe-autopilot-check-task.log"

Set-Location $Root

# Force Python and PowerShell output to UTF-8 so the task log stays readable.
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

function Write-TaskLog {
    param(
        [AllowEmptyString()]
        [string]$Message
    )

    $Message | Out-File -FilePath $LogPath -Append -Encoding utf8
}

$Stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-TaskLog "[$Stamp] Starting NothingButA Safe Autopilot Check"

try {
    $Output = & python $PythonScript 2>&1
    $ExitCode = $LASTEXITCODE

    foreach ($Line in $Output) {
        if ($null -eq $Line) {
            Write-TaskLog ""
        }
        else {
            Write-TaskLog $Line.ToString()
        }
    }

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
        backup_path = RUNNER_PATH.with_suffix(f".ps1.bak-allow-empty-log-lines-{timestamp}")
        shutil.copy2(RUNNER_PATH, backup_path)

        RUNNER_PATH.write_text(NEW_RUNNER, encoding="utf-8")

        print("NOTHINGBUTA RUNNER EMPTY-LINE LOG PATCH: PASS")
        print("backup:", backup_path)
        print("runner:", RUNNER_PATH)
        return 0

    except Exception as exc:
        logger.exception("Runner patch failed")
        print("NOTHINGBUTA RUNNER EMPTY-LINE LOG PATCH: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
