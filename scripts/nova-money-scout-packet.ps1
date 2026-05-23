$ErrorActionPreference = "Stop"

function Write-PacketLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )

    Write-Host "[Nova Money Packet][$Level] $Message"
}

try {
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $moneyDir = Join-Path $workspace "money_scout"
    $dataDir = Join-Path $workspace "data"
    $logsDir = Join-Path $workspace "logs"
    $heartbeatPath = Join-Path $workspace "heartbeat\latest-heartbeat.md"
    $policyPath = Join-Path $moneyDir "MONEY_SCOUT_POLICY.md"
    $queuePath = Join-Path $dataDir "money_scout_queue.json"
    $workLogPath = Join-Path $dataDir "work_log.json"

    foreach ($file in @($policyPath, $queuePath, $workLogPath)) {
        if (-not (Test-Path $file)) {
            throw "Required file missing: $file"
        }
    }

    $policy = Get-Content $policyPath -Raw
    $queueRaw = Get-Content $queuePath -Raw
    $workLogRaw = Get-Content $workLogPath -Raw

    $queue = $queueRaw | ConvertFrom-Json
    $workLog = $workLogRaw | ConvertFrom-Json

    $ideaCount = @($queue.ideas).Count
    $activeIdeas = @($queue.ideas | Where-Object { $_.status -in @("research_only", "review_ready", "approved_by_chris", "build_ready") })
    $approvalNeeded = @($queue.ideas | Where-Object { $_.status -eq "review_ready" })

    $heartbeatSummary = if (Test-Path $heartbeatPath) {
        (Get-Content $heartbeatPath -TotalCount 35) -join "`n"
    }
    else {
        "No heartbeat file found."
    }

    $lastLogEntries = @($workLog.entries | Select-Object -Last 3) | ConvertTo-Json -Depth 8

    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $generatedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

    $packetLines = @(
        "NOVA MONEY SCOUT COMPACT PACKET",
        "",
        "Generated At:",
        $generatedAt,
        "",
        "Workspace:",
        $workspace,
        "",
        "Critical Rules:",
        "PowerShell read local files and injected this compact packet.",
        "Nova must not claim direct file access.",
        "Nova must not invent market evidence.",
        "Nova must not perform external actions.",
        "Nova must ask Chris before spending, publishing, outreach, account creation, affiliate changes, commits, pushes, or live site changes.",
        "",
        "Money Scout Counts:",
        "Total ideas: $ideaCount",
        "Active ideas: $(@($activeIdeas).Count)",
        "Ideas needing Chris approval: $(@($approvalNeeded).Count)",
        "",
        "Heartbeat Summary:",
        $heartbeatSummary,
        "",
        "Money Scout Policy:",
        $policy,
        "",
        "Current Queue JSON:",
        $queueRaw,
        "",
        "Last 3 Work Log Entries:",
        $lastLogEntries,
        "",
        "Task:",
        "Review the Money Scout state.",
        "If there are zero ideas, recommend the safest local-only next step to create research-only candidate ideas.",
        "Do not invent evidence.",
        "Do not claim income is guaranteed.",
        "Do not recommend external actions yet.",
        "",
        "Required Response Format:",
        "1. Current State",
        "2. Money Scout Queue Status",
        "3. Anti-Hallucination Risks",
        "4. Safest Next Local-Only Action",
        "5. Exact Command or File Change",
        "6. Proof Needed",
        "",
        "Required final line:",
        "NOVA_MONEY_SCOUT_READY"
    )

    $packet = $packetLines -join "`r`n"
    $packetPath = Join-Path $logsDir "nova-money-scout-packet-$stamp.txt"

    Set-Content -Path $packetPath -Value $packet -Encoding UTF8
    Set-Clipboard -Value $packet

    Write-PacketLog "Money Scout packet created."
    Write-PacketLog "Saved to: $packetPath"
    Write-PacketLog "Copied to clipboard."
    Write-PacketLog "Paste into Nova TUI with Ctrl+V, then Enter."
}
catch {
    Write-Error "[Nova Money Packet] FAILED: $($_.Exception.Message)"
    exit 1
}
