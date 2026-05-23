param(
    [string]$Source = "nova",
    [string]$EventType = "info",
    [string]$Level = "INFO",
    [string]$Message = "",
    [string]$CycleId = "",
    [string]$StepName = "",
    [string]$DetailsJson = "{}",
    [string]$DetailsBase64 = ""
)

$ErrorActionPreference = "Stop"

try {
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $logsDir = Join-Path $workspace "logs"
    $reportsDir = Join-Path $workspace "reports"

    New-Item -ItemType Directory -Force -Path $logsDir, $reportsDir | Out-Null

    $jsonlPath = Join-Path $logsDir "nova-activity-feed.jsonl"
    $jsonReportPath = Join-Path $reportsDir "nova-live-activity-feed.json"

    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss-fff"
    $eventId = "act-$stamp"

    # Details are intentionally structured JSON so later dashboard cards can
    # filter or group activity by step, score, category, or safety gate.
    # Prefer Base64 so PowerShell command-line parsing cannot strip JSON quotes.
    try {
        if (-not [string]::IsNullOrWhiteSpace($DetailsBase64)) {
            $decoded = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($DetailsBase64))
            $details = $decoded | ConvertFrom-Json
        }
        else {
            $details = $DetailsJson | ConvertFrom-Json
        }
    }
    catch {
        $details = [pscustomobject]@{
            parse_error = $true
            raw = $(if (-not [string]::IsNullOrWhiteSpace($DetailsBase64)) { $DetailsBase64 } else { $DetailsJson })
        }
    }

    $event = [pscustomobject]@{
        event_id = $eventId
        timestamp = $now
        level = $Level
        source = $Source
        cycle_id = $CycleId
        step_name = $StepName
        event_type = $EventType
        message = $Message
        details = $details
    }

    $line = $event | ConvertTo-Json -Depth 20 -Compress

    # JSONL is append-friendly and safe for a live activity feed.
    Add-Content -Path $jsonlPath -Value $line -Encoding UTF8

    # Keep the dashboard report small: newest 150 events only.
    $lines = Get-Content $jsonlPath -Tail 150

    $events = @()
    foreach ($item in $lines) {
        if ([string]::IsNullOrWhiteSpace($item)) {
            continue
        }

        try {
            $events += ($item | ConvertFrom-Json)
        }
        catch {
            # Skip malformed lines so one bad write does not kill the dashboard.
            continue
        }
    }

    $report = [pscustomobject]@{
        schema_version = "1.0"
        updated_at = $now
        source = $jsonlPath
        event_count = @($events).Count
        events = $events
    }

    $report | ConvertTo-Json -Depth 30 | Set-Content -Path $jsonReportPath -Encoding UTF8
}
catch {
    Write-Error "[Activity Log] FAILED: $($_.Exception.Message)"
    exit 1
}

