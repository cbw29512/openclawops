try {
    $ErrorActionPreference = "Stop"

    $Root = "C:\Users\dmchris\OpenClawOps"
    $DashboardDir = Join-Path $Root "dashboard"
    $FreezePyPath = Join-Path $Root "scripts\nova_nothingbuta_release_freeze.py"

    if (-not (Test-Path $FreezePyPath)) {
        throw "Missing freeze Python script: $FreezePyPath"
    }

    Set-Location $DashboardDir
    .\.venv\Scripts\python.exe $FreezePyPath
}
catch {
    Write-Host "`nNOTHINGBUTA RELEASE FREEZE: FAIL" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}