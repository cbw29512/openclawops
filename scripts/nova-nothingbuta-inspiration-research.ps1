try {
    $ErrorActionPreference = "Stop"

    $Root = "C:\Users\dmchris\OpenClawOps"
    $DashboardDir = Join-Path $Root "dashboard"
    $RepairPyPath = Join-Path $Root "scripts\nova_nothingbuta_inspiration_repair.py"

    if (-not (Test-Path $RepairPyPath)) {
        throw "Missing Python runner: $RepairPyPath"
    }

    Set-Location $DashboardDir
    .\.venv\Scripts\python.exe $RepairPyPath
}
catch {
    Write-Host "`nNOTHINGBUTA INSPIRATION RESEARCH RUN: FAIL" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}