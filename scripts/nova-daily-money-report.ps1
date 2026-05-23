$ErrorActionPreference = "Stop"

function Write-ReportLog {
    param([string]$Message, [string]$Level = "INFO")
    Write-Host "[Daily Money Report][$Level] $Message"
}

function Read-JsonSafe {
    param([string]$Path, [string]$Label)

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

try {
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $reportsDir = Join-Path $workspace "reports"
    $dataDir = Join-Path $workspace "data"
    $opsDir = Join-Path $reportsDir "ops-cycle"

    $latestCyclePath = Join-Path $opsDir "latest-cycle.json"
    $auditPath = Join-Path $reportsDir "nova-enterprise-audit.json"
    $queuePath = Join-Path $reportsDir "source-review-queue.json"
    $indexPath = Join-Path $dataDir "opportunity_index.json"
    $artifactPath = Join-Path $dataDir "artifact_registry.json"

    $jsonOutPath = Join-Path $reportsDir "daily-money-report.json"
    $mdOutPath = Join-Path $reportsDir "daily-money-report.md"

    $cycle = Read-JsonSafe -Path $latestCyclePath -Label "latest ops cycle"
    $audit = Read-JsonSafe -Path $auditPath -Label "enterprise audit"
    $queue = Read-JsonSafe -Path $queuePath -Label "source review queue"
    $index = Read-JsonSafe -Path $indexPath -Label "opportunity index"
    $artifacts = Read-JsonSafe -Path $artifactPath -Label "artifact registry"

    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

    $positiveItems = @($queue.items |
        Where-Object { $_.recommended_dashboard_bucket -eq "positive_queue" } |
        Sort-Object priority_index -Descending |
        Select-Object -First 5)

    $needsChris = @($queue.items |
        Where-Object { $_.recommended_dashboard_bucket -eq "needs_chris_signal" } |
        Sort-Object priority_index -Descending |
        Select-Object -First 10)

    $pitItems = @($queue.items |
        Where-Object { $_.recommended_dashboard_bucket -eq "idea_pit" } |
        Sort-Object priority_index |
        Select-Object -First 10)

    $activePositiveCount = @($index.items | Where-Object { $_.status -eq "active_positive" }).Count
    $activeWatchCount = @($index.items | Where-Object { $_.status -eq "active_watch" }).Count
    $ideaPitCount = @($index.items | Where-Object { $_.status -eq "idea_pit" -or $_.status -eq "deep_freeze" }).Count
    $artifactCount = @($artifacts.artifacts).Count

    $recommendedNextAction = "Review Needs Chris Signal and Boost/Bury. Keep external actions disabled."

    if ($audit.totals.fail -gt 0) {
        $recommendedNextAction = "Stop. Enterprise audit has failures."
    }
    elseif ($audit.totals.warn -gt 0) {
        $recommendedNextAction = "Fix audit warnings before building dashboard features."
    }
    elseif ($queue.counts.needs_chris_signal -gt 0) {
        $recommendedNextAction = "Use Boost +1 / Bury -1 on Needs Chris Signal items to train Nova priorities."
    }
    elseif ($queue.counts.positive_queue -gt 0) {
        $recommendedNextAction = "Let Nova improve positive local artifacts and research adjacent angles."
    }

    $report = [pscustomobject]@{
        generated_at = $now
        latest_cycle = [pscustomobject]@{
            cycle_id = $cycle.cycle_id
            status = $cycle.status
            generated_at = $cycle.generated_at
        }
        audit = $audit.totals
        source_review_queue = $queue.counts
        opportunity_index = [pscustomobject]@{
            active_positive = $activePositiveCount
            active_watch = $activeWatchCount
            idea_pit = $ideaPitCount
        }
        artifacts = [pscustomobject]@{
            total = $artifactCount
        }
        top_positive_items = $positiveItems
        chris_attention_required = $needsChris
        idea_pit = $pitItems
        recommended_next_action = $recommendedNextAction
        safety = "Local reports only. No publishing, selling, outreach, sending messages, commits, pushes, spending, credentials, affiliate changes, or live-site changes."
    }

    $report | ConvertTo-Json -Depth 40 | Set-Content -Path $jsonOutPath -Encoding UTF8

    $md = @()
    $md += "# Daily Money Report"
    $md += ""
    $md += "Generated At: $now"
    $md += ""
    $md += "## System Health"
    $md += "- Latest Cycle: $($cycle.cycle_id)"
    $md += "- Cycle Status: $($cycle.status)"
    $md += "- Audit Pass: $($audit.totals.pass)"
    $md += "- Audit Warn: $($audit.totals.warn)"
    $md += "- Audit Fail: $($audit.totals.fail)"
    $md += "- Audit Info: $($audit.totals.info)"
    $md += ""
    $md += "## Queue Counts"
    $md += "- Needs Chris Signal: $($queue.counts.needs_chris_signal)"
    $md += "- Positive Queue: $($queue.counts.positive_queue)"
    $md += "- Watch Queue: $($queue.counts.watch_queue)"
    $md += "- Idea Pit: $($queue.counts.idea_pit)"
    $md += "- Artifacts: $artifactCount"
    $md += ""
    $md += "## Recommended Next Action"
    $md += $recommendedNextAction
    $md += ""
    $md += "## Positive Queue"

    foreach ($item in $positiveItems) {
        $md += ""
        $md += "### $($item.item_id)"
        $md += "- Title: $($item.title)"
        $md += "- Priority Index: $($item.priority_index)"
        $md += "- Artifact: $($item.artifact_id)"
        $md += "- Next: $($item.recommended_next_action)"
    }

    $md += ""
    $md += "## Needs Chris Signal"

    foreach ($item in $needsChris) {
        $md += ""
        $md += "### $($item.item_id)"
        $md += "- Title: $($item.title)"
        $md += "- Priority Index: $($item.priority_index)"
        $md += "- Evidence Quality: $($item.evidence_quality)"
        $md += "- Source URL: $($item.source_url)"
        $md += "- Decision: Boost +1 for more local research, or Bury -1 to park."
    }

    $md += ""
    $md += "## Safety"
    $md += $report.safety

    $md | Set-Content -Path $mdOutPath -Encoding UTF8

    Write-ReportLog "Daily money report created."
    Write-ReportLog "Markdown: $mdOutPath"
    Write-ReportLog "JSON: $jsonOutPath"
}
catch {
    Write-Error "[Daily Money Report] FAILED: $($_.Exception.Message)"
    exit 1
}
