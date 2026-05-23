param(
    [Parameter(Mandatory = $true)]
    [string]$ItemId,

    [Parameter(Mandatory = $true)]
    [ValidateSet("approve", "disapprove")]
    [string]$Vote,

    [string]$Note = ""
)

$ErrorActionPreference = "Stop"

function Write-VoteLog {
    param([string]$Message, [string]$Level = "INFO")
    Write-Host "[Opportunity Vote][$Level] $Message"
}

function Get-StatusFromPriority {
    param([int]$Priority)

    if ($Priority -ge 3) { return "active_positive" }
    if ($Priority -ge 1) { return "active_watch" }
    if ($Priority -eq 0) { return "neutral_hold" }
    if ($Priority -ge -2) { return "idea_pit" }
    return "deep_freeze"
}

function Get-NextAction {
    param([string]$Status)

    switch ($Status) {
        "active_positive" { return "Work harder locally: improve artifact, research adjacent angles, prepare stronger review packet." }
        "active_watch" { return "Check lightly: look for new evidence, improve only if signal strengthens." }
        "neutral_hold" { return "Hold: wait for Chris vote or new evidence." }
        "idea_pit" { return "Park: do not spend active cycles unless new evidence appears." }
        "deep_freeze" { return "Deep freeze: preserve for dedupe only unless strong new evidence appears." }
        default { return "Review state." }
    }
}

try {
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $dataDir = Join-Path $workspace "data"
    $reportsDir = Join-Path $workspace "reports"

    $indexPath = Join-Path $dataDir "opportunity_index.json"
    $reportPath = Join-Path $reportsDir "opportunity-index-report.md"

    if (-not (Test-Path $indexPath)) {
        throw "Missing opportunity index. Run nova-opportunity-index-init.ps1 first."
    }

    Copy-Item $indexPath "$indexPath.bak-$(Get-Date -Format yyyyMMdd-HHmmss)"

    $index = Get-Content $indexPath -Raw | ConvertFrom-Json
    $item = @($index.items | Where-Object { $_.item_id -eq $ItemId }) | Select-Object -First 1

    if ($null -eq $item) {
        throw "Item not found: $ItemId"
    }

    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
    $delta = if ($Vote -eq "approve") { 1 } else { -1 }

    $item.priority_index = [int]$item.priority_index + $delta
    $item.status = Get-StatusFromPriority -Priority ([int]$item.priority_index)
    $item.work_mode = if ($item.priority_index -gt 0) { "work_harder" } elseif ($item.priority_index -lt 0) { "parked" } else { "hold" }
    $item.next_ai_action = Get-NextAction -Status $item.status

    if ($Vote -eq "approve") {
        $item.chris_votes.approve_count = [int]$item.chris_votes.approve_count + 1
    }
    else {
        $item.chris_votes.disapprove_count = [int]$item.chris_votes.disapprove_count + 1
    }

    $item.chris_votes.last_vote = $Vote
    $item.chris_votes.last_voted_at = $now

    $item.history = @($item.history) + [pscustomobject]@{
        event = "chris_$Vote"
        delta = $delta
        priority_index_after = $item.priority_index
        at = $now
        note = $Note
    }

    $index.updated_at = $now
    $index | ConvertTo-Json -Depth 40 | Set-Content -Path $indexPath -Encoding UTF8

    $report = @()
    $report += "# Opportunity Index Report"
    $report += ""
    $report += "Generated At: $now"
    $report += ""
    $report += "## Counts"

    $index.items | Group-Object status | ForEach-Object {
        $report += "- $($_.Name): $($_.Count)"
    }

    $report += ""
    $report += "## Items"

    foreach ($i in ($index.items | Sort-Object priority_index -Descending)) {
        $report += ""
        $report += "### $($i.item_id)"
        $report += "- Title: $($i.title)"
        $report += "- Priority Index: $($i.priority_index)"
        $report += "- Status: $($i.status)"
        $report += "- Last Vote: $($i.chris_votes.last_vote)"
        $report += "- Next AI Action: $($i.next_ai_action)"
    }

    $report | Set-Content -Path $reportPath -Encoding UTF8

    Write-VoteLog "$Vote applied to $ItemId. Delta: $delta"
    Write-VoteLog "New priority index: $($item.priority_index)"
    Write-VoteLog "New status: $($item.status)"
}
catch {
    Write-Error "[Opportunity Vote] FAILED: $($_.Exception.Message)"
    exit 1
}
