$ErrorActionPreference = "Stop"

try {
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $dataDir = Join-Path $workspace "data"
    $reportsDir = Join-Path $workspace "reports"
    $libPath = Join-Path $workspace "scripts\lib\internet-scout-lib.ps1"

    if (-not (Test-Path $libPath)) {
        throw "Missing library file: $libPath"
    }

    . $libPath

    $inboxPath = Join-Path $dataDir "internet_idea_inbox.json"
    $registryPath = Join-Path $dataDir "internet_seen_registry.json"
    $sourceHealthPath = Join-Path $reportsDir "internet-source-health.json"
    $reportMdPath = Join-Path $reportsDir "internet-auto-discover-v2-report.md"
    $reportJsonPath = Join-Path $reportsDir "internet-auto-discover-v2-report.json"

    foreach ($file in @($inboxPath, $registryPath, $sourceHealthPath)) {
        if (-not (Test-Path $file)) {
            throw "Missing required file: $file"
        }
    }

    $backupStamp = Get-Date -Format yyyyMMdd-HHmmss
    Copy-Item $inboxPath "$inboxPath.bak-$backupStamp"
    Copy-Item $registryPath "$registryPath.bak-$backupStamp"

    $inbox = Get-Content $inboxPath -Raw | ConvertFrom-Json
    $registry = Get-Content $registryPath -Raw | ConvertFrom-Json
    $sourceHealth = Get-Content $sourceHealthPath -Raw | ConvertFrom-Json

    Ensure-ArrayProperty -Object $inbox -Name "ideas"
    Ensure-ArrayProperty -Object $registry -Name "seen_urls"
    Ensure-ArrayProperty -Object $registry -Name "title_fingerprints"
    Ensure-ArrayProperty -Object $registry -Name "content_fingerprints"
    Ensure-ArrayProperty -Object $registry -Name "history"

    $healthySources = @($sourceHealth.results | Where-Object {
        $_.reachable -eq $true -and $_.items_found -gt 0 -and $_.feed_format -in @("rss", "atom")
    })

    $sourceStats = @()
    $addedTotal = 0
    $duplicateTotal = 0
    $lowSignalTotal = 0
    $checkedTotal = 0
    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

    foreach ($source in $healthySources) {
        Write-ScoutLog "Scanning $($source.name)"

        $stats = [pscustomobject]@{
            source_name = $source.name
            source_url = $source.url
            feed_format = $source.feed_format
            items_found = 0
            checked = 0
            added = 0
            skipped_duplicate = 0
            skipped_low_signal = 0
            errors = @()
        }

        try {
            $response = Invoke-WebRequest `
                -Uri $source.url `
                -UseBasicParsing `
                -Headers @{ "User-Agent" = "NovaMoneyScout/2.0 local evidence collector" } `
                -TimeoutSec 20

            [xml]$xml = $response.Content
            $items = @(Get-FeedItems -Xml $xml)
            $stats.items_found = $items.Count

            foreach ($item in ($items | Select-Object -First 25)) {
                $stats.checked += 1
                $checkedTotal += 1

                if ([string]::IsNullOrWhiteSpace($item.title) -or [string]::IsNullOrWhiteSpace($item.link)) {
                    continue
                }

                $normalizedUrl = Get-NormalizedUrl $item.link
                $titleFingerprint = Get-TitleFingerprint $item.title
                $contentFingerprint = Get-ContentFingerprint -Title $item.title -Url $item.link

                $isDuplicate =
                    (@($registry.seen_urls) -contains $normalizedUrl) -or
                    (@($registry.title_fingerprints) -contains $titleFingerprint) -or
                    (@($registry.content_fingerprints) -contains $contentFingerprint)

                if ($isDuplicate) {
                    $stats.skipped_duplicate += 1
                    $duplicateTotal += 1
                    continue
                }

                $score = Get-OpportunityScore -Title $item.title -Summary $item.description
                $decision = "skipped_low_signal"

                if ($score.total -lt 6) {
                    $stats.skipped_low_signal += 1
                    $lowSignalTotal += 1
                }
                else {
                    $ideaId = Get-NextIdeaId -Inbox $inbox
                    $status = if ($score.total -ge 8) { "evidence_pending" } else { "source_review_required" }
                    $decision = $status

                    $summary = if ([string]::IsNullOrWhiteSpace($item.description)) {
                        "Feed item had title and URL but no usable summary."
                    }
                    else {
                        $item.description.Substring(0, [Math]::Min(500, $item.description.Length))
                    }

                    $idea = [pscustomobject]@{
                        idea_id = $ideaId
                        status = $status
                        title = $item.title
                        source_url = $item.link
                        normalized_url = $normalizedUrl
                        source_name = $source.name
                        source_type = "rss_atom_auto_discovery"
                        feed_format = $item.feed_format
                        claim_supported = "A public feed item produced a local opportunity score of $($score.total). This does not prove demand or revenue."
                        evidence_summary = $summary
                        evidence_quality = "feed_title_summary"
                        audience = "unknown"
                        pain_point = "unknown until reviewed"
                        proposed_solution = "pending AI review"
                        monetization_model = "unknown"
                        confidence = "low"
                        created_at = $now
                        opportunity_score = $score
                        title_fingerprint = $titleFingerprint
                        content_fingerprint = $contentFingerprint
                        risk_flags = @("unverified source", "no revenue proof", "requires evidence review")
                        approval_required_before = @(
                            "spending",
                            "publishing",
                            "outreach",
                            "account_creation",
                            "affiliate_link_change",
                            "commit",
                            "push",
                            "live_site_change"
                        )
                    }

                    $inbox.ideas = @($inbox.ideas) + $idea
                    $stats.added += 1
                    $addedTotal += 1
                }

                $registry.seen_urls = @($registry.seen_urls) + $normalizedUrl
                $registry.title_fingerprints = @($registry.title_fingerprints) + $titleFingerprint
                $registry.content_fingerprints = @($registry.content_fingerprints) + $contentFingerprint
                $registry.history = @($registry.history) + [pscustomobject]@{
                    idea_id = if ($decision -in @("evidence_pending", "source_review_required")) { $inbox.ideas[-1].idea_id } else { "" }
                    title = $item.title
                    source_url = $item.link
                    normalized_url = $normalizedUrl
                    title_fingerprint = $titleFingerprint
                    content_fingerprint = $contentFingerprint
                    first_seen_at = $now
                    source_name = $source.name
                    source_type = "rss_atom_auto_discovery"
                    decision = $decision
                    opportunity_score_total = $score.total
                }
            }
        }
        catch {
            $stats.errors += $_.Exception.Message
        }

        $sourceStats += $stats
    }

    $inbox.updated_at = $now
    $registry.updated_at = $now

    $inbox | ConvertTo-Json -Depth 40 | Set-Content -Path $inboxPath -Encoding UTF8
    $registry | ConvertTo-Json -Depth 40 | Set-Content -Path $registryPath -Encoding UTF8

    $runReport = [pscustomobject]@{
        generated_at = $now
        healthy_sources_used = @($healthySources).Count
        checked_total = $checkedTotal
        added_total = $addedTotal
        skipped_duplicate_total = $duplicateTotal
        skipped_low_signal_total = $lowSignalTotal
        source_stats = $sourceStats
        safety = "No publishing, outreach, spending, commits, pushes, affiliate changes, account creation, credential use, or live changes performed."
    }

    $runReport | ConvertTo-Json -Depth 40 | Set-Content -Path $reportJsonPath -Encoding UTF8

    $md = @()
    $md += "# Internet Auto Discover V2 Report"
    $md += ""
    $md += "Generated At: $now"
    $md += ""
    $md += "- Healthy sources used: $($runReport.healthy_sources_used)"
    $md += "- Checked total: $checkedTotal"
    $md += "- Added total: $addedTotal"
    $md += "- Skipped duplicates: $duplicateTotal"
    $md += "- Skipped low signal: $lowSignalTotal"
    $md += ""
    $md += "## Source Stats"

    foreach ($s in $sourceStats) {
        $md += ""
        $md += "### $($s.source_name)"
        $md += "- Feed format: $($s.feed_format)"
        $md += "- Items found: $($s.items_found)"
        $md += "- Checked: $($s.checked)"
        $md += "- Added: $($s.added)"
        $md += "- Skipped duplicate: $($s.skipped_duplicate)"
        $md += "- Skipped low signal: $($s.skipped_low_signal)"
        $md += "- Errors: $($s.errors -join '; ')"
    }

    $md += ""
    $md += "## Safety"
    $md += $runReport.safety

    $md | Set-Content -Path $reportMdPath -Encoding UTF8

    Write-ScoutLog "Auto-discovery V2 complete."
    Write-ScoutLog "Checked: $checkedTotal"
    Write-ScoutLog "Added: $addedTotal"
    Write-ScoutLog "Skipped duplicates: $duplicateTotal"
    Write-ScoutLog "Skipped low signal: $lowSignalTotal"
    Write-ScoutLog "Report: $reportMdPath"
}
catch {
    Write-Error "[Internet Auto Discover V2] FAILED: $($_.Exception.Message)"
    exit 1
}
