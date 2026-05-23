$ErrorActionPreference = "Stop"

function Write-QueueLog {
    param([string]$Message, [string]$Level = "INFO")
    Write-Host "[Source Review Queue][$Level] $Message"
}

function Read-JsonSafe {
    param(
        [Parameter(Mandatory = $true)] [string]$Path,
        [Parameter(Mandatory = $true)] [string]$Label
    )

    if (-not (Test-Path $Path)) {
        throw "Missing $Label file: $Path"
    }

    try {
        return Get-Content $Path -Raw | ConvertFrom-Json
    }
    catch {
        throw "Invalid JSON in $Label file: $Path :: $($_.Exception.Message)"
    }
}

function Get-Bucket {
    param(
        [string]$SourceStatus,
        [string]$IndexStatus,
        [int]$PriorityIndex,
        [string]$ArtifactId
    )

    if ($IndexStatus -eq "idea_pit" -or $IndexStatus -eq "deep_freeze") {
        return "idea_pit"
    }

    if ($SourceStatus -eq "review_ready" -or -not [string]::IsNullOrWhiteSpace($ArtifactId)) {
        return "positive_queue"
    }

    if ($SourceStatus -eq "source_review_required" -and $PriorityIndex -ge 1) {
        return "needs_chris_signal"
    }

    if ($IndexStatus -eq "active_watch") {
        return "watch_queue"
    }

    return "neutral_hold"
}

function Get-RecommendedAction {
    param(
        [string]$Bucket,
        [string]$EvidenceQuality
    )

    switch ($Bucket) {
        "positive_queue" {
            return "Nova should work locally: improve artifact, research adjacent angles, and prepare stronger review packet."
        }
        "needs_chris_signal" {
            return "Chris should Boost +1 for more local research or Bury -1 to park. Evidence is not enough for external action."
        }
        "watch_queue" {
            return "Nova should check lightly for new evidence before spending more local effort."
        }
        "idea_pit" {
            return "Park. Preserve for dedupe memory only unless new evidence revives it."
        }
        default {
            return "Hold until new evidence or Chris vote."
        }
    }
}

try {
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $dataDir = Join-Path $workspace "data"
    $reportsDir = Join-Path $workspace "reports"

    $inboxPath = Join-Path $dataDir "internet_idea_inbox.json"
    $indexPath = Join-Path $dataDir "opportunity_index.json"
    $artifactPath = Join-Path $dataDir "artifact_registry.json"
    $jsonPath = Join-Path $reportsDir "source-review-queue.json"
    $mdPath = Join-Path $reportsDir "source-review-queue.md"

    $inbox = Read-JsonSafe -Path $inboxPath -Label "internet inbox"
    $index = Read-JsonSafe -Path $indexPath -Label "opportunity index"
    $artifactRegistry = Read-JsonSafe -Path $artifactPath -Label "artifact registry"

    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
    $queueItems = @()

    foreach ($idx in @($index.items)) {
        $idea = @($inbox.ideas | Where-Object { $_.idea_id -eq $idx.idea_id }) | Select-Object -First 1
        $artifact = @($artifactRegistry.artifacts | Where-Object { $_.idea_id -eq $idx.idea_id }) | Select-Object -First 1

        if ($null -eq $idea) {
            continue
        }

        $artifactId = ""
        if ($null -ne $artifact) {
            $artifactId = $artifact.artifact_id
        }

        $priority = [int]$idx.priority_index
        $bucket = Get-Bucket -SourceStatus $idea.status -IndexStatus $idx.status -PriorityIndex $priority -ArtifactId $artifactId
        $evidenceQuality = ""
        if ($idea.PSObject.Properties.Name -contains "evidence_quality") {
            $evidenceQuality = [string]$idea.evidence_quality
        }

        $queueItems += [pscustomobject]@{
            item_id = $idx.item_id
            idea_id = $idea.idea_id
            artifact_id = $artifactId
            title = $idea.title
            source_status = $idea.status
            index_status = $idx.status
            priority_index = $priority
            evidence_quality = $evidenceQuality
            source_url = $idea.source_url
            last_vote = $idx.chris_votes.last_vote
            approve_count = $idx.chris_votes.approve_count
            disapprove_count = $idx.chris_votes.disapprove_count
            recommended_dashboard_bucket = $bucket
            recommended_next_action = Get-RecommendedAction -Bucket $bucket -EvidenceQuality $evidenceQuality
            boost_command = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$env:USERPROFILE\OpenClawOps\scripts\nova-opportunity-vote.ps1`" -ItemId `"$($idx.item_id)`" -Vote approve"
            bury_command = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$env:USERPROFILE\OpenClawOps\scripts\nova-opportunity-vote.ps1`" -ItemId `"$($idx.item_id)`" -Vote disapprove"
        }
    }

    $summary = [pscustomobject]@{
        generated_at = $now
        counts = [pscustomobject]@{
            needs_chris_signal = @($queueItems | Where-Object { $_.recommended_dashboard_bucket -eq "needs_chris_signal" }).Count
            positive_queue = @($queueItems | Where-Object { $_.recommended_dashboard_bucket -eq "positive_queue" }).Count
            watch_queue = @($queueItems | Where-Object { $_.recommended_dashboard_bucket -eq "watch_queue" }).Count
            idea_pit = @($queueItems | Where-Object { $_.recommended_dashboard_bucket -eq "idea_pit" }).Count
            neutral_hold = @($queueItems | Where-Object { $_.recommended_dashboard_bucket -eq "neutral_hold" }).Count
        }
        items = $queueItems
        safety = "This report is read-only. Boost/Bury changes only opportunity_index.json and does not authorize external action."
    }

    $summary | ConvertTo-Json -Depth 30 | Set-Content -Path $jsonPath -Encoding UTF8

    $md = @()
    $md += "# Source Review Queue"
    $md += ""
    $md += "Generated At: $now"
    $md += ""
    $md += "## Counts"
    $md += "- Needs Chris Signal: $($summary.counts.needs_chris_signal)"
    $md += "- Positive Queue: $($summary.counts.positive_queue)"
    $md += "- Watch Queue: $($summary.counts.watch_queue)"
    $md += "- Idea Pit: $($summary.counts.idea_pit)"
    $md += "- Neutral Hold: $($summary.counts.neutral_hold)"
    $md += ""
    $md += "## Needs Chris Signal"

    foreach ($item in ($queueItems | Where-Object { $_.recommended_dashboard_bucket -eq "needs_chris_signal" } | Sort-Object priority_index -Descending)) {
        $md += ""
        $md += "### $($item.item_id)"
        $md += "- Title: $($item.title)"
        $md += "- Idea ID: $($item.idea_id)"
        $md += "- Priority Index: $($item.priority_index)"
        $md += "- Source Status: $($item.source_status)"
        $md += "- Evidence Quality: $($item.evidence_quality)"
        $md += "- Source URL: $($item.source_url)"
        $md += "- Recommended Action: $($item.recommended_next_action)"
        $md += "- Boost Target: $($item.item_id)"
        $md += "- Bury Target: $($item.item_id)"
    }

    $md += ""
    $md += "## Positive Queue"

    foreach ($item in ($queueItems | Where-Object { $_.recommended_dashboard_bucket -eq "positive_queue" } | Sort-Object priority_index -Descending)) {
        $md += ""
        $md += "### $($item.item_id)"
        $md += "- Title: $($item.title)"
        $md += "- Priority Index: $($item.priority_index)"
        $md += "- Artifact: $($item.artifact_id)"
        $md += "- Recommended Action: $($item.recommended_next_action)"
    }

    $md += ""
    $md += "## Idea Pit"

    foreach ($item in ($queueItems | Where-Object { $_.recommended_dashboard_bucket -eq "idea_pit" } | Sort-Object priority_index)) {
        $md += ""
        $md += "### $($item.item_id)"
        $md += "- Title: $($item.title)"
        $md += "- Priority Index: $($item.priority_index)"
        $md += "- Recommended Action: $($item.recommended_next_action)"
    }

    $md += ""
    $md += "## Safety"
    $md += $summary.safety

    $md | Set-Content -Path $mdPath -Encoding UTF8

    Write-QueueLog "Source review queue created."
    Write-QueueLog "Markdown: $mdPath"
    Write-QueueLog "JSON: $jsonPath"
}
catch {
    Write-Error "[Source Review Queue] FAILED: $($_.Exception.Message)"
    exit 1
}
