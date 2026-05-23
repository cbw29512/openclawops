$ErrorActionPreference = "Stop"

try {
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $heartbeatDir = Join-Path $workspace "heartbeat"

    New-Item -ItemType Directory -Force -Path $heartbeatDir | Out-Null

    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $generatedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

    $openclawStatus = try { openclaw status 2>&1 | Out-String } catch { "openclaw status failed: $($_.Exception.Message)" }
    $gatewayStatus = try { openclaw gateway status 2>&1 | Out-String } catch { "gateway status failed: $($_.Exception.Message)" }
    $ollamaList = try { ollama list 2>&1 | Out-String } catch { "ollama list failed: $($_.Exception.Message)" }

    $report = @"
# Nova Local Heartbeat

Generated At: $generatedAt

Computer: $env:COMPUTERNAME
User: $env:USERNAME
Workspace: $workspace

## Summary

Nova heartbeat ran locally.

This is inspection-only. It does not publish, upload, message, delete, commit, push, spend money, or modify live systems.

## OpenClaw Status

$openclawStatus

## Gateway Status

$gatewayStatus

## Ollama Models

$ollamaList

## Next Safe Action

Review this heartbeat report. No approval-gated action was performed.
"@

    $latestPath = Join-Path $heartbeatDir "latest-heartbeat.md"
    $archivePath = Join-Path $heartbeatDir "heartbeat-$stamp.md"

    Set-Content -Path $latestPath -Value $report -Encoding UTF8
    Set-Content -Path $archivePath -Value $report -Encoding UTF8

    Write-Host "[PASS] Heartbeat written:"
    Write-Host $latestPath
}
catch {
    Write-Error "[FAIL] Nova heartbeat failed: $($_.Exception.Message)"
    exit 1
}
