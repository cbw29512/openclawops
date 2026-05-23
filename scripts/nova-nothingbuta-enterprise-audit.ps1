try {
    $ErrorActionPreference = "Stop"

    $Root = "C:\Users\dmchris\OpenClawOps"
    $DashboardDir = Join-Path $Root "dashboard"
    $AuditPyPath = Join-Path $Root "scripts\nova_nothingbuta_enterprise_audit.py"

    if (-not (Test-Path $AuditPyPath)) {
        throw "Missing audit Python script: $AuditPyPath"
    }

    Set-Location $DashboardDir
    .\.venv\Scripts\python.exe $AuditPyPath
}
catch {
    Write-Host "`nNOTHINGBUTA ENTERPRISE AUDIT: FAIL" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}