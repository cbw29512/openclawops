$ErrorActionPreference = "Stop"

function Write-ScoreLog {
    param([string]$Message, [string]$Level = "INFO")
    Write-Host "[Internet Opportunity Score][$Level] $Message"
}

function Test-MatchAny {
    param(
        [string]$Text,
        [string[]]$Terms
    )

    foreach ($term in $Terms) {
        if ($Text -match [regex]::Escape($term)) {
            return $true
        }
    }

    return $false
}

try {
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $dataDir = Join-Path $workspace "data"
    $reportsDir = Join-Path $workspace "reports"

    $inboxPath = Join-Path $dataDir "internet_idea_inbox.json"
    $reportPath = Join-Path $reportsDir "internet-opportunity-score-report.md"

    if (-not (Test-Path $inboxPath)) {
        throw "Missing inbox file: $inboxPath"
    }

    $backupPath = "$inboxPath.bak-$(Get-Date -Format yyyyMMdd-HHmmss)"
    Copy-Item $inboxPath $backupPath

    $inbox = Get-Content $inboxPath -Raw | ConvertFrom-Json

    if (-not ($inbox.PSObject.Properties.Name -contains "ideas")) {
        throw "Inbox has no ideas array."
    }

    $buyerTerms = @(
        "small business", "customer", "client", "paid", "pricing", "buy",
        "sales", "revenue", "budget", "owner", "freelancer", "agency"
    )

    $painTerms = @(
        "problem", "help", "struggle", "need", "looking for", "can't",
        "manual", "takes too long", "expensive", "workflow", "spam",
        "waste", "hard", "stuck"
    )

    $monetizationTerms = @(
        "affiliate", "template", "course", "newsletter", "lead", "SaaS",
        "tool", "prompt", "checklist", "service", "landing page", "product"
    )

    $testabilityTerms = @(
        "template", "checklist", "prompt", "landing page", "workflow",
        "tool", "guide", "audit", "review", "generator", "script"
    )

    $noiseTerms = @(
        "lawsuit", "acquires", "acquisition", "pope", "encyclical",
        "co-founder", "radio stations", "lost his lawsuit", "press release"
    )

    $scored = 0
    $parked = 0
    $needsReview = 0
    $promoted = 0
    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

    $reportLines = @(
        "# Internet Opportunity Score Report",
        "",
        "Generated At: $now",
        "",
        "## Scored Ideas",
        ""
    )

    foreach ($idea in @($inbox.ideas)) {
        if ($idea.status -notin @("raw_discovery", "source_review_required")) {
            continue
        }

        $text = "$($idea.title) $($idea.evidence_summary) $($idea.claim_supported)".ToLowerInvariant()

        $buyerSignal = if (Test-MatchAny -Text $text -Terms $buyerTerms) { 2 } else { 0 }
        $painSignal = if (Test-MatchAny -Text $text -Terms $painTerms) { 2 } else { 0 }
        $monetizationSignal = if (Test-MatchAny -Text $text -Terms $monetizationTerms) { 2 } else { 0 }
        $testabilitySignal = if (Test-MatchAny -Text $text -Terms $testabilityTerms) { 2 } else { 0 }
        $evidenceQuality = if ($idea.evidence_quality -eq "title_url_only") { 0 } else { 2 }
        $noisePenalty = if (Test-MatchAny -Text $text -Terms $noiseTerms) { 3 } else { 0 }

        $total = $buyerSignal + $painSignal + $monetizationSignal + $testabilitySignal + $evidenceQuality - $noisePenalty

        if (-not ($idea.PSObject.Properties.Name -contains "opportunity_score")) {
            $idea | Add-Member -MemberType NoteProperty -Name opportunity_score -Value ([pscustomobject]@{})
        }

        $idea.opportunity_score = [pscustomobject]@{
            buyer_signal = $buyerSignal
            pain_signal = $painSignal
            monetization_signal = $monetizationSignal
            testability_signal = $testabilitySignal
            evidence_quality = $evidenceQuality
            noise_penalty = $noisePenalty
            total = $total
        }

        if (-not ($idea.PSObject.Properties.Name -contains "scored_at")) {
            $idea | Add-Member -MemberType NoteProperty -Name scored_at -Value $now
        }
        else {
            $idea.scored_at = $now
        }

        if (-not ($idea.PSObject.Properties.Name -contains "score_reason")) {
            $idea | Add-Member -MemberType NoteProperty -Name score_reason -Value ""
        }

        if ($total -ge 8 -and $idea.evidence_quality -ne "title_url_only") {
            $idea.status = "evidence_pending"
            $idea.score_reason = "High enough opportunity score with usable evidence. Still requires review before any action."
            $promoted += 1
        }
        elseif ($total -ge 6) {
            $idea.status = "source_review_required"
            $idea.score_reason = "Potential signal exists, but evidence is not strong enough for promotion."
            $needsReview += 1
        }
        else {
            $idea.status = "parked_low_signal"
            $idea.score_reason = "Low buyer/pain/testability signal or high news/noise penalty. Preserved for dedupe memory but not worth action now."
            $parked += 1
        }

        $scored += 1

        $reportLines += "- $($idea.idea_id): $($idea.title)"
        $reportLines += "  - status: $($idea.status)"
        $reportLines += "  - score: $total"
        $reportLines += "  - reason: $($idea.score_reason)"
        $reportLines += ""
    }

    $inbox.updated_at = $now

    $inbox | ConvertTo-Json -Depth 30 | Set-Content -Path $inboxPath -Encoding UTF8
    Get-Content $inboxPath -Raw | ConvertFrom-Json | Out-Null

    $reportLines += "## Totals"
    $reportLines += ""
    $reportLines += "- Scored: $scored"
    $reportLines += "- Promoted to evidence_pending: $promoted"
    $reportLines += "- Source review required: $needsReview"
    $reportLines += "- Parked low signal: $parked"
    $reportLines += ""
    $reportLines += "## Safety"
    $reportLines += ""
    $reportLines += "No publishing, outreach, spending, commits, pushes, affiliate changes, or live changes were performed."

    $reportLines | Set-Content -Path $reportPath -Encoding UTF8

    Write-ScoreLog "Scored ideas: $scored"
    Write-ScoreLog "Promoted to evidence_pending: $promoted"
    Write-ScoreLog "Source review required: $needsReview"
    Write-ScoreLog "Parked low signal: $parked"
    Write-ScoreLog "Report: $reportPath"
}
catch {
    Write-Error "[Internet Opportunity Score] FAILED: $($_.Exception.Message)"
    exit 1
}
