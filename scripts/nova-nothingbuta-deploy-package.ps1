try {
    $ErrorActionPreference = "Stop"

    $Root = "C:\Users\dmchris\OpenClawOps"
    $DashboardDir = Join-Path $Root "dashboard"
    $DeployPyPath = Join-Path $Root "scripts\nova_nothingbuta_deploy_package.py"

    if (-not (Test-Path $DeployPyPath)) {
        throw "Missing deploy Python script: $DeployPyPath"
    }

    Set-Location $DashboardDir
    .\.venv\Scripts\python.exe $DeployPyPath
}
catch {
    Write-Host "`nNOTHINGBUTA DEPLOY PACKAGE: FAIL" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}