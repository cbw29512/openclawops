$ErrorActionPreference = "Stop"

function Write-PacketLog {
    param([string]$Message, [string]$Level = "INFO")
    Write-Host "[Internet Scout Packet][$Level] $Message"
}

try {
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $moneyDir = Join-Path $workspace "money_scout"
    $dataDir = Join-Path $workspace "data"
    $logsDir = Join-Path $workspace "logs"

    $policyPath = Join-Path $moneyDir "INTERNET_SCOUT_POLICY.md"
    $sourcesPath = Join-Path $dataDir "internet_research_sources.json"
    $inboxPath = Join-Path $dataDir "internet_idea_inbox.json"
    $moneyQueuePath = Join-Path $dataDir "money_scout_queue.json"

    foreach ($file in @($policyPath, $sourcesPath, $inboxPath, $moneyQueuePath)) {
        if (-not (Test-Path $file)) { throw "Missing required file: $file" }
    }

    $policy = Get-Content $policyPath -Raw
    $sourcesRaw = Get-Content $sourcesPath -Raw
    $inboxRaw = Get-Content $inboxPath -Raw
    $queueRaw = Get-Content $moneyQueuePath -Raw

    $sources = $sourcesRaw | ConvertFrom-Json
    $inbox = $inboxRaw | ConvertFrom-Json
    $queue = $queueRaw | ConvertFrom-Json

    $enabledSources = @($sources.sources | Where-Object { $_.enabled -eq $true }).Count
    $rawIdeas = @($inbox.ideas | Where-Object { $_.status -eq "raw_discovery" }).Count
    $pendingIdeas = @($inbox.ideas | Where-Object { $_.status -eq "evidence_pending" }).Count
    $reviewReady = @($inbox.ideas | Where-Object { $_.status -eq "review_ready" }).Count
    $moneyScoutIdeas = @($queue.ideas).Count

    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $generatedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

    $packetLines = @(
        "NOVA INTERNET SCOUT PACKET",
        "",
        "Generated At:",
        $generatedAt,
        "",
        "Critical Rules:",
        "PowerShell read local files and injected this compact packet.",
        "Nova must not invent internet evidence.",
        "Nova must not claim any idea is proven without a source URL or proof.",
        "Nova must not perform external actions.",
        "Chris approval is required before publishing, outreach, spending, account creation, affiliate changes, commits, pushes, or live site changes.",
        "",
        "Counts:",
        "enabled_sources: $enabledSources",
        "internet_raw_discoveries: $rawIdeas",
        "internet_evidence_pending: $pendingIdeas",
        "internet_review_ready: $reviewReady",
        "existing_money_scout_ideas: $moneyScoutIdeas",
        "",
        "Policy:",
        $policy,
        "",
        "Sources JSON:",
        $sourcesRaw,
        "",
        "Internet Idea Inbox JSON:",
        $inboxRaw,
        "",
        "Task:",
        "Review the Internet Scout system state.",
        "Confirm this is safe for non-hallucinating 24/7 opportunity discovery.",
        "Recommend the next local-only source/intake improvement.",
        "Do not invent market evidence.",
        "Do not suggest external execution yet.",
        "",
        "Required final line:",
        "NOVA_INTERNET_SCOUT_READY"
    )

    $packet = $packetLines -join "`r`n"
    $packetPath = Join-Path $logsDir "nova-internet-scout-packet-$stamp.txt"

    Set-Content -Path $packetPath -Value $packet -Encoding UTF8
    Set-Clipboard -Value $packet

    Write-PacketLog "Internet Scout packet created."
    Write-PacketLog "Saved to: $packetPath"
    Write-PacketLog "Copied to clipboard."
}
catch {
    Write-Error "[Internet Scout Packet] FAILED: $($_.Exception.Message)"
    exit 1
}
