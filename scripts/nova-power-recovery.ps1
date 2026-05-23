$ErrorActionPreference = "Stop"

try {
    Start-Sleep -Seconds 20

    openclaw gateway restart | Out-String | Out-File "$env:USERPROFILE\OpenClawOps\heartbeat\power-recovery.log" -Append -Encoding utf8

    Start-Sleep -Seconds 5

    powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\OpenClawOps\scripts\nova-heartbeat.ps1" |
        Out-File "$env:USERPROFILE\OpenClawOps\heartbeat\power-recovery.log" -Append -Encoding utf8

    "[PASS] Nova power recovery ran at $(Get-Date)" |
        Out-File "$env:USERPROFILE\OpenClawOps\heartbeat\power-recovery.log" -Append -Encoding utf8
}
catch {
    "[FAIL] Nova power recovery failed at $(Get-Date): $($_.Exception.Message)" |
        Out-File "$env:USERPROFILE\OpenClawOps\heartbeat\power-recovery.log" -Append -Encoding utf8
    exit 1
}
