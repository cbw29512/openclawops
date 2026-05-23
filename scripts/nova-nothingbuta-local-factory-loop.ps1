try {
    $ErrorActionPreference = "Stop"

    $Root = "C:\Users\dmchris\OpenClawOps"
    $DashboardDir = Join-Path $Root "dashboard"
    $PythonScriptPath = Join-Path $Root "scripts\nova_nothingbuta_local_factory_loop.py"

    if (-not (Test-Path $PythonScriptPath)) {
        throw "Missing Python factory loop: $PythonScriptPath"
    }

    $env:PYTHONIOENCODING = "utf-8"
    $env:NOTHINGBUTA_FACTORY_BATCH = "10"

    if (Test-Path (Join-Path $DashboardDir ".venv\Scripts\python.exe")) {
        Set-Location $DashboardDir
        .\.venv\Scripts\python.exe $PythonScriptPath
    }
    else {
        python $PythonScriptPath
    }
}
catch {
    Write-Host "
NOTHINGBUTA MODULE-SHELL FACTORY LOOP: FAIL" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}