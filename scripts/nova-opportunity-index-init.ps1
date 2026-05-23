$ErrorActionPreference = "Stop"

function Write-IndexLog {
    param([string]$Message, [string]$Level = "INFO")
    Write-Host "[Opportunity Index][$Level] $Message"
}

function Get-StatusFromPriority {
    param([int]$Priority)

    if ($Priority -ge 3) { return "active_positive" }
    if ($Priority -ge 1) { return "active_watch" }
    if ($Priority -eq 0) { return "neutral_hold" }
    if ($Priority -ge -2) { return "idea_pit" }
    return "deep_freeze"
}

function Get-BasePriority {
    param($Idea, $Artifact)

    $score = 0

    if ($Idea.status -eq "review_ready") { $score += 2 }
    elseif ($Idea.status -eq "source_review_required") { $score += 1 }
    elseif ($Idea.status -eq "parked_low_signal") { $score -= 1 }

    if ($null -ne $Artifact) { $score += 1 }

    return $score
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

    $inboxPath = Join-Path $dataDir "internet_idea_inbox.json"
    $artifactRegistryPath = Join-Path $dataDir "artifact_registry.json"
    $indexPath = Join-Path $dataDir "opportunity_index.json"
    $reportPath = Join-Path $reportsDir "opportunity-index-report.md"

    foreach ($file in @($inboxPath, $artifactRegistryPath)) {
        if (-not (Test-Path $file)) {
            throw "Missing required file: $file"
        }
    }

    if (Test-Path $indexPath) {
        Copy-Item $indexPath "$indexPath.bak-$(Get-Date -Format yyyyMMdd-HHmmss)"
        $existingIndex = Get-Content $indexPath -Raw | ConvertFrom-Json
        $existingItems = @($existingIndex.items)
    }
    else {
        $existingItems = @()
    }

    $inbox = Get-Content $inboxPath -Raw | ConvertFrom-Json
    $artifactRegistry = Get-Content $artifactRegistryPath -Raw | ConvertFrom-Json

    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
    $items = @()

    foreach ($idea in @($inbox.ideas)) {
        $artifact = @($artifactRegistry.artifacts | Where-Object { $_.idea_id -eq $idea.idea_id }) | Select-Object -First 1
        $existing = @($existingItems | Where-Object { $_.idea_id -eq $idea.idea_id }) | Select-Object -First 1

        if ($null -ne $existing) {
            $priority = [int]$existing.priority_index
            $votes = $existing.chris_votes
            $history = @($existing.history)
        }
        else {
            $priority = Get-BasePriority -Idea $idea -Artifact $artifact
            $votes = [pscustomobject]@{
                approve_count = 0
                disapprove_count = 0
                last_vote = ""
                last_voted_at = ""
            }
            $history = @(
                [pscustomobject]@{
                    event = "index_created"
                    delta = $priority
                    priority_index_after = $priority
                    at = $now
                    note = "Initial index score from idea status and artifact presence."
                }
            )
        }

        $status = Get-StatusFromPriority -Priority $priority

        $sourceScore = 0
        if ($idea.opportunity_score -and $idea.opportunity_score.total -ne $null) {
            $sourceScore = [int]$idea.opportunity_score.total
        }

        $artifactId = ""
        if ($null -ne $artifact) {
            $artifactId = $artifact.artifact_id
        }

        $items += [pscustomobject]@{
            item_id = "idx-$($idea.idea_id)"
            idea_id = $idea.idea_id
            artifact_id = $artifactId
            title = $idea.title
            source_status = $idea.status
            status = $status
            priority_index = $priority
            chris_votes = $votes
            ai_signals = [pscustomobject]@{
                source_score = $sourceScore
                new_evidence_score = 0
                market_signal_score = 0
                artifact_quality_score = if ($artifactId) { 1 } else { 0 }
            }
            work_mode = if ($priority -gt 0) { "work_harder" } elseif ($priority -lt 0) { "parked" } else { "hold" }
            next_ai_action = Get-NextAction -Status $status
            approval_gate = [pscustomobject]@{
                local_work_allowed = $true
                external_action_allowed = $false
                requires_chris_before = @(
                    "publishing",
                    "selling",
                    "outreach",
                    "commit",
                    "push",
                    "spending",
                    "live_site_change",
                    "affiliate_change",
                    "legal_claim"
                )
            }
            history = $history
        }
    }

    $index = [pscustomobject]@{
        schema_version = "1.0"
        updated_at = $now
        items = $items
    }

    $index | ConvertTo-Json -Depth 40 | Set-Content -Path $indexPath -Encoding UTF8

    $report = @()
    $report += "# Opportunity Index Report"
    $report += ""
    $report += "Generated At: $now"
    $report += ""
    $report += "## Counts"
    $report += ""

    $items | Group-Object status | ForEach-Object {
        $report += "- $($_.Name): $($_.Count)"
    }

    $report += ""
    $report += "## Items"

    foreach ($item in ($items | Sort-Object priority_index -Descending)) {
        $report += ""
        $report += "### $($item.item_id)"
        $report += "- Title: $($item.title)"
        $report += "- Priority Index: $($item.priority_index)"
        $report += "- Status: $($item.status)"
        $report += "- Source Status: $($item.source_status)"
        $report += "- Artifact: $($item.artifact_id)"
        $report += "- Next AI Action: $($item.next_ai_action)"
    }

    $report += ""
    $report += "## Safety"
    $report += ""
    $report += "Approve/Bury only changes local priority. It does not authorize external action."

    $report | Set-Content -Path $reportPath -Encoding UTF8

    Write-IndexLog "Opportunity index updated."
    Write-IndexLog "Index: $indexPath"
    Write-IndexLog "Report: $reportPath"
}
catch {
    Write-Error "[Opportunity Index] FAILED: $($_.Exception.Message)"
    exit 1
}
