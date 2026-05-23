$ErrorActionPreference = "Stop"

function Write-LearningLog {
    param([string]$Message, [string]$Level = "INFO")
    Write-Host "[Learning Ledger][$Level] $Message"
}

function Read-JsonOrNull {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return $null
    }

    try {
        return Get-Content $Path -Raw | ConvertFrom-Json
    }
    catch {
        throw "Invalid JSON: $Path :: $($_.Exception.Message)"
    }
}

function Add-Unique {
    param(
        [array]$List,
        [string]$Value
    )

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return @($List)
    }

    if (@($List) -notcontains $Value) {
        return @($List) + $Value
    }

    return @($List)
}

try {
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $dataDir = Join-Path $workspace "data"
    $reportsDir = Join-Path $workspace "reports"

    New-Item -ItemType Directory -Force -Path $dataDir, $reportsDir | Out-Null

    $ledgerPath = Join-Path $dataDir "learning_ledger.json"
    $reportPath = Join-Path $reportsDir "learning-loop-report.md"

    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

    if (Test-Path $ledgerPath) {
        Copy-Item $ledgerPath "$ledgerPath.bak-$(Get-Date -Format yyyyMMdd-HHmmss)"
        $ledger = Read-JsonOrNull -Path $ledgerPath
    }
    else {
        $ledger = [pscustomobject]@{
            schema_version = "1.0"
            created_at = $now
            updated_at = $now
            learning_mode = "evidence_based"
            summary = [pscustomobject]@{
                total_events = 0
                boost_votes = 0
                bury_votes = 0
                artifacts_created = 0
                audit_warnings = 0
                audit_failures = 0
                simulation_attempts = 0
                high_simulation_scores = 0
                weak_simulation_scores = 0
                roi_winners = 0
                roi_losers = 0
            }
            events = @()
            rules_learned = @()
            patterns_to_repeat = @()
            patterns_to_avoid = @()
        }
    }

    $dailyReportPath = Join-Path $reportsDir "daily-money-report.json"
    $auditPath = Join-Path $reportsDir "nova-enterprise-audit.json"
    $indexPath = Join-Path $dataDir "opportunity_index.json"
    $artifactPath = Join-Path $dataDir "artifact_registry.json"
    $experimentLedgerPath = Join-Path $dataDir "experiment_ledger.json"
    $simulationRunPath = Join-Path $reportsDir "nova-simulation-research-run.json"
$finderFeeCategoryPath = Join-Path $reportsDir "finder-fee-category-simulation.json"

    $daily = Read-JsonOrNull -Path $dailyReportPath
    $audit = Read-JsonOrNull -Path $auditPath
    $index = Read-JsonOrNull -Path $indexPath
    $artifacts = Read-JsonOrNull -Path $artifactPath
    $experimentLedger = Read-JsonOrNull -Path $experimentLedgerPath
    $simulationRun = Read-JsonOrNull -Path $simulationRunPath
$finderFeeCategoryRun = Read-JsonOrNull -Path $finderFeeCategoryPath

    $events = @($ledger.events)

    if ($null -ne $daily) {
        $eventId = "learn-cycle-$((Get-Date).ToString('yyyyMMdd-HHmmss'))"

        $events += [pscustomobject]@{
            event_id = $eventId
            event_type = "daily_report_snapshot"
            created_at = $now
            evidence_source = $dailyReportPath
            summary = "Daily report snapshot captured for learning."
            metrics = [pscustomobject]@{
                audit_pass = $daily.audit.pass
                audit_warn = $daily.audit.warn
                audit_fail = $daily.audit.fail
                needs_chris_signal = $daily.source_review_queue.needs_chris_signal
                positive_queue = $daily.source_review_queue.positive_queue
                idea_pit = $daily.source_review_queue.idea_pit
                artifacts_total = $daily.artifacts.total
            }
            lesson = "Use current queue/audit state to guide local priority decisions."
        }
    }

    if ($null -ne $simulationRun) {
        $events += [pscustomobject]@{
            event_id = "learn-sim-$($simulationRun.run_id)"
            event_type = "simulation_research_snapshot"
            created_at = $now
            evidence_source = $simulationRunPath
            summary = "Simulation research run captured for learning."
            metrics = [pscustomobject]@{
                run_id = $simulationRun.run_id
                attempts = @($simulationRun.attempts).Count
                high_scores = @($simulationRun.attempts | Where-Object { [int]$_.simulation_score -ge 10 }).Count
                medium_scores = @($simulationRun.attempts | Where-Object { [int]$_.simulation_score -ge 6 -and [int]$_.simulation_score -lt 10 }).Count
                weak_scores = @($simulationRun.attempts | Where-Object { [int]$_.simulation_score -lt 3 }).Count
                measured_revenue_usd = 0
                measured_spend_usd = 0
                measured_roi_percent = 0
            }
            lesson = "Simulation scores can prioritize local research, but they do not prove real demand, revenue, or ROI."
        }
    }

    if ($null -ne $finderFeeCategoryRun) {
        $events += [pscustomobject]@{
            event_id = "learn-finder-cat-$($finderFeeCategoryRun.run_id)"
            event_type = "finder_fee_category_simulation_snapshot"
            created_at = $now
            evidence_source = $finderFeeCategoryPath
            summary = "Finder Fee category simulation captured for learning."
            metrics = [pscustomobject]@{
                run_id = $finderFeeCategoryRun.run_id
                top_categories = @($finderFeeCategoryRun.top_categories).Count
                high_category_scores = @($finderFeeCategoryRun.top_categories | Where-Object { [int]$_.simulation_score -ge 8 }).Count
                measured_revenue_usd = 0
                measured_spend_usd = 0
                measured_roi_percent = 0
            }
            lesson = "Finder Fee category simulations can identify promising research niches, but they do not prove real buyer demand or ROI."
        }
    }

    $boostVotes = 0
    $buryVotes = 0

    if ($null -ne $index) {
        foreach ($item in @($index.items)) {
            if ($item.chris_votes.approve_count -gt 0) {
                $boostVotes += [int]$item.chris_votes.approve_count
            }

            if ($item.chris_votes.disapprove_count -gt 0) {
                $buryVotes += [int]$item.chris_votes.disapprove_count
            }
        }
    }

    $artifactCount = 0
    if ($null -ne $artifacts) {
        $artifactCount = @($artifacts.artifacts).Count
    }

    $auditWarnings = 0
    $auditFailures = 0

    if ($null -ne $audit) {
        $auditWarnings = [int]$audit.totals.warn
        $auditFailures = [int]$audit.totals.fail
    }

    $simulationAttempts = 0
    $highSimulationScores = 0
    $weakSimulationScores = 0
    $simulationRepeatPatterns = @()
$finderFeeRepeatPatterns = @()
    $simulationAvoidPatterns = @()

    if ($null -ne $finderFeeCategoryRun) {
        foreach ($cat in @($finderFeeCategoryRun.top_categories)) {
            if (
                $null -ne $cat -and
                -not [string]::IsNullOrWhiteSpace([string]$cat.category_id) -and
                [int]$cat.simulation_score -ge 8
            ) {
                $finderFeeRepeatPatterns += "Finder Fee category signal: $($cat.category_id) — $($cat.category_name) scored $($cat.simulation_score). Stronger niche because it is specific, searchable, and low-risk enough for local match-packet simulation."
            }
        }
    }

    if ($null -ne $experimentLedger) {
        foreach ($experiment in @($experimentLedger.experiments)) {
            foreach ($attempt in @($experiment.simulation_attempts)) {
                # Defensive guard:
                # Older/planned experiments may not have real simulation_attempts yet.
                # PowerShell can treat missing/null collections as one blank item.
                # We skip those so Nova does not learn fake weak patterns.
                if ($null -eq $attempt) {
                    continue
                }

                $itemId = [string]$attempt.item_id
                $title = [string]$attempt.title
                $scoreRaw = $attempt.simulation_score

                if (
                    [string]::IsNullOrWhiteSpace($itemId) -or
                    [string]::IsNullOrWhiteSpace($title) -or
                    $null -eq $scoreRaw
                ) {
                    continue
                }

                $score = [int]$scoreRaw
                $simulationAttempts += 1

                if ($score -ge 10) {
                    $highSimulationScores += 1
                    $simulationRepeatPatterns += "High simulation score: $itemId — $title scored $score. Continue local simulation and prepare stronger packet."
                }

                if ($score -lt 3) {
                    $weakSimulationScores += 1
                    $simulationAvoidPatterns += "Weak simulation score: $itemId — $title scored $score. If repeated, recommend Bury -1."
                }
            }
        }
    }

    $ledger.updated_at = $now
    $ledger.events = $events
    $ledger.summary = [pscustomobject]@{
        total_events = @($events).Count
        boost_votes = $boostVotes
        bury_votes = $buryVotes
        artifacts_created = $artifactCount
        audit_warnings = $auditWarnings
        audit_failures = $auditFailures
        simulation_attempts = $simulationAttempts
        high_simulation_scores = $highSimulationScores
        weak_simulation_scores = $weakSimulationScores
        roi_winners = 0
        roi_losers = 0
    }

    $repeatPatterns = @()
    $avoidPatterns = @()
    $rulesLearned = @()

    if ($boostVotes -gt 0) {
        $repeatPatterns += "Chris Boost votes indicate which opportunity types deserve more local work."
    }

    if ($artifactCount -gt 0) {
        $repeatPatterns += "Review-ready items with source-backed evidence can produce local artifacts safely."
    }

    foreach ($pattern in $simulationRepeatPatterns) {
        $repeatPatterns = Add-Unique -List $repeatPatterns -Value $pattern
    }

    foreach ($pattern in $finderFeeRepeatPatterns) {
        $repeatPatterns = Add-Unique -List $repeatPatterns -Value $pattern
    }

    if ($auditWarnings -gt 0) {
        $avoidPatterns += "Do not promote weak summaries or parser artifacts without source review."
    }

    if ($auditFailures -gt 0) {
        $avoidPatterns += "Stop local automation when enterprise audit fails."
    }

    foreach ($pattern in $simulationAvoidPatterns) {
        $avoidPatterns = Add-Unique -List $avoidPatterns -Value $pattern
    }

    $rulesLearned += "Evidence quality must control promotion."
    $rulesLearned += "Boost/Bury votes adjust local priority only, not external authority."
    $rulesLearned += "Simulation scores prioritize local research only; they do not prove revenue, demand, conversion, or ROI."
    $rulesLearned += "ROI must be measured before budget increases."
$rulesLearned += "Finder Fee category scores prioritize local niche research only; they do not prove paying customers."

    $ledger.rules_learned = $rulesLearned
    $ledger.patterns_to_repeat = $repeatPatterns
    $ledger.patterns_to_avoid = $avoidPatterns

    $ledger | ConvertTo-Json -Depth 60 | Set-Content -Path $ledgerPath -Encoding UTF8

    $md = @()
    $md += "# Learning Loop Report"
    $md += ""
    $md += "Generated At: $now"
    $md += ""
    $md += "## Summary"
    $md += "- Total Events: $($ledger.summary.total_events)"
    $md += "- Boost Votes: $($ledger.summary.boost_votes)"
    $md += "- Bury Votes: $($ledger.summary.bury_votes)"
    $md += "- Artifacts Created: $($ledger.summary.artifacts_created)"
    $md += "- Audit Warnings: $($ledger.summary.audit_warnings)"
    $md += "- Audit Failures: $($ledger.summary.audit_failures)"
    $md += "- Simulation Attempts: $($ledger.summary.simulation_attempts)"
    $md += "- High Simulation Scores: $($ledger.summary.high_simulation_scores)"
    $md += "- Weak Simulation Scores: $($ledger.summary.weak_simulation_scores)"
    $md += "- ROI Winners: $($ledger.summary.roi_winners)"
    $md += "- ROI Losers: $($ledger.summary.roi_losers)"
    $md += ""
    $md += "## Rules Learned"

    foreach ($rule in @($ledger.rules_learned)) {
        $md += "- $rule"
    }

    $md += ""
    $md += "## Patterns To Repeat"

    foreach ($pattern in @($ledger.patterns_to_repeat)) {
        $md += "- $pattern"
    }

    $md += ""
    $md += "## Patterns To Avoid"

    foreach ($pattern in @($ledger.patterns_to_avoid)) {
        $md += "- $pattern"
    }

    $md += ""
    $md += "## Safety"
    $md += "Learning changes future local prioritization only. It does not authorize publishing, selling, outreach, sending messages, commits, pushes, spending, credentials, affiliate changes, or live-site changes."

    $md | Set-Content -Path $reportPath -Encoding UTF8

    Write-LearningLog "Learning ledger updated."
    Write-LearningLog "Ledger: $ledgerPath"
    Write-LearningLog "Report: $reportPath"
}
catch {
    Write-Error "[Learning Ledger] FAILED: $($_.Exception.Message)"
    exit 1
}


