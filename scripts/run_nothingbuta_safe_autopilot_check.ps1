$ErrorActionPreference = "Stop"

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
