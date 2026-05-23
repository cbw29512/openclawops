$ErrorActionPreference = "Stop"

function Write-RankLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )

    Write-Host "[Nova Money Scout Rank][$Level] $Message"
}

try {
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $moneyDir = Join-Path $workspace "money_scout"
    $dataDir = Join-Path $workspace "data"
    $logsDir = Join-Path $workspace "logs"

    $queuePath = Join-Path $dataDir "money_scout_queue.json"
    $workLogPath = Join-Path $dataDir "work_log.json"
    $activeExperimentPath = Join-Path $moneyDir "active_experiment.json"

    foreach ($file in @($queuePath, $workLogPath)) {
        if (-not (Test-Path $file)) {
            throw "Required file missing: $file"
        }
    }

    $queue = Get-Content $queuePath -Raw | ConvertFrom-Json
    $workLog = Get-Content $workLogPath -Raw | ConvertFrom-Json

    $ideas = @($queue.ideas)

    if ($ideas.Count -eq 0) {
        throw "No Money Scout ideas found."
    }

    $ranked = $ideas |
        Sort-Object `
            @{Expression = { [int]$_.score.total }; Descending = $true},
            @{Expression = { [int]$_.score.speed_to_test }; Descending = $true},
            @{Expression = { [int]$_.score.risk }; Descending = $false}

    $winner = $ranked | Select-Object -First 1
    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"

    $activeExperiment = [pscustomobject]@{
        schema_version = "1.0"
        experiment_id = "exp-0001"
        idea_id = $winner.idea_id
        title = $winner.title
        status = "research_only"
        created_at = $now
        selected_reason = "Highest current score with local-only next action available. This does not prove demand or revenue."
        next_safe_action = "Create local QA checklist and evidence packet. No publishing or external action."
        approval_required_before = @(
            "spending",
            "publishing",
            "outreach",
            "affiliate_link_change",
            "commit",
            "push",
            "live_site_change"
        )
    }

    $activeExperiment | ConvertTo-Json -Depth 10 | Set-Content -Path $activeExperimentPath -Encoding UTF8

    if (-not ($workLog.PSObject.Properties.Name -contains "entries")) {
        $workLog | Add-Member -MemberType NoteProperty -Name entries -Value @()
    }

    $workEntry = [pscustomobject]@{
        event = "Money Scout selected active research-only experiment"
        status = "success"
        created_at = $now
        notes = "Selected $($winner.idea_id): $($winner.title). No external action performed."
    }

    $workLog.entries = @($workLog.entries) + $workEntry
    $workLog | ConvertTo-Json -Depth 10 | Set-Content -Path $workLogPath -Encoding UTF8

    $rankSummary = $ranked | ForEach-Object {
        "- $($_.idea_id): $($_.title) | total=$($_.score.total) | speed=$($_.score.speed_to_test) | risk=$($_.score.risk) | status=$($_.status)"
    }

    $packetLines = @(
        "NOVA MONEY SCOUT RANKING PACKET",
        "",
        "Generated At:",
        $now,
        "",
        "Critical Rules:",
        "PowerShell ranked existing local Money Scout candidates.",
        "Nova must not invent evidence.",
        "Nova must not claim revenue is proven.",
        "Nova must not perform external actions.",
        "Chris approval is required before publishing, affiliate changes, commits, pushes, outreach, spending, or live changes.",
        "",
        "Ranked Candidates:",
        ($rankSummary -join "`r`n"),
        "",
        "Selected Active Experiment:",
        "Experiment: exp-0001",
        "Idea: $($winner.idea_id)",
        "Title: $($winner.title)",
        "Status: research_only",
        "",
        "Next Safe Local-Only Action:",
        "Create a QA checklist and evidence packet for the selected idea.",
        "",
        "Task for Nova:",
        "Review this ranking.",
        "Confirm the selected experiment.",
        "Recommend the exact local-only QA checklist fields needed next.",
        "Do not suggest publishing, outreach, affiliate changes, commits, pushes, or spending.",
        "",
        "Required final line:",
        "NOVA_MONEY_RANKING_READY"
    )

    $packet = $packetLines -join "`r`n"
    $packetPath = Join-Path $logsDir "nova-money-ranking-packet-$stamp.txt"

    Set-Content -Path $packetPath -Value $packet -Encoding UTF8
    Set-Clipboard -Value $packet

    Write-RankLog "Selected: $($winner.idea_id) - $($winner.title)"
    Write-RankLog "Active experiment saved: $activeExperimentPath"
    Write-RankLog "Ranking packet saved: $packetPath"
    Write-RankLog "Packet copied to clipboard. Paste into Nova TUI."
}
catch {
    Write-Error "[Nova Money Scout Rank] FAILED: $($_.Exception.Message)"
    exit 1
}
