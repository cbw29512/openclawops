try {
    $ErrorActionPreference = "Stop"

    $Root = "C:\Users\dmchris\OpenClawOps"
    $DashboardDir = Join-Path $Root "dashboard"

    if (-not (Test-Path $DashboardDir)) {
        throw "Missing dashboard directory: $DashboardDir"
    }

    Set-Location $DashboardDir

    $PythonCode = @"
from __future__ import annotations

import sys
from pathlib import Path

dashboard_dir = Path(r"C:\Users\dmchris\OpenClawOps\dashboard")

# The temporary Python file runs from %TEMP%, so Python cannot automatically
# import the local dashboard package unless we explicitly add dashboard/ to sys.path.
if str(dashboard_dir) not in sys.path:
    sys.path.insert(0, str(dashboard_dir))

from app.nothingbuta_research_guidance import apply_builder_context_to_queue

result = apply_builder_context_to_queue()

print("NOTHINGBUTA BUILDER CONTEXT: PASS")
print("Status:", result.get("status"))
print("Candidate count:", result.get("candidate_count"))
"@

    $TempPy = Join-Path $env:TEMP "nothingbuta_builder_context_runner.py"
    $Encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($TempPy, $PythonCode, $Encoding)

    .\.venv\Scripts\python.exe $TempPy
}
catch {
    Write-Host "`nNOTHINGBUTA BUILDER CONTEXT: FAIL" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}