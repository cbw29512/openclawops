$ErrorActionPreference = "Stop"

function Write-AuditLog {
    param([string]$Message, [string]$Level = "INFO")
    Write-Host "[Nova Enterprise Audit][$Level] $Message"
}

try {
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $dataDir = Join-Path $workspace "data"
    $moneyDir = Join-Path $workspace "money_scout"
    $scriptsDir = Join-Path $workspace "scripts"
    $reportsDir = Join-Path $workspace "reports"
    $heartbeatPath = Join-Path $workspace "heartbeat\latest-heartbeat.md"

    New-Item -ItemType Directory -Force -Path $reportsDir | Out-Null

    $reportPath = Join-Path $reportsDir "nova-enterprise-audit.md"
    $jsonPath = Join-Path $reportsDir "nova-enterprise-audit.json"

    $findings = @()

    function Add-Finding {
        param(
            [string]$Area,
            [string]$Status,
            [string]$Severity,
            [string]$Detail,
            [string]$NextAction
        )

        $script:findings += [pscustomobject]@{
            area = $Area
            status = $Status
            severity = $Severity
            detail = $Detail
            next_action = $NextAction
        }
    }

    function Read-JsonSafe {
        param([string]$Path, [string]$Area)

        if (-not (Test-Path $Path)) {
            Add-Finding $Area "fail" "high" "Missing file: $Path" "Create or restore the file."
            return $null
        }

        try {
            return Get-Content $Path -Raw | ConvertFrom-Json
        }
        catch {
            Add-Finding $Area "fail" "high" "Invalid JSON: $Path" "Repair JSON or restore backup."
            return $null
        }
    }

    # Gateway check.
    $gateway = (& openclaw gateway status 2>&1 | Out-String)

    if ($gateway -match "Connectivity probe:\s+ok") {
        Add-Finding "gateway" "pass" "low" "OpenClaw gateway connectivity probe is OK." "No action."
    }
    else {
        Add-Finding "gateway" "fail" "high" "OpenClaw gateway probe is not OK." "Run openclaw gateway restart."
    }

    # Heartbeat check.
    if (Test-Path $heartbeatPath) {
        $age = [math]::Round(((Get-Date) - (Get-Item $heartbeatPath).LastWriteTime).TotalMinutes, 1)

        if ($age -le 90) {
            Add-Finding "heartbeat" "pass" "low" "Heartbeat is recent: $age minutes old." "No action."
        }
        else {
            Add-Finding "heartbeat" "warn" "medium" "Heartbeat is stale: $age minutes old." "Check scheduled task."
        }
    }
    else {
        Add-Finding "heartbeat" "fail" "high" "latest-heartbeat.md missing." "Run nova-heartbeat.ps1."
    }

    # Money Scout files.
    $moneyQueue = Read-JsonSafe (Join-Path $dataDir "money_scout_queue.json") "money_scout_queue"
    if ($null -ne $moneyQueue) {
        Add-Finding "money_scout_queue" "pass" "low" "Money Scout ideas: $(@($moneyQueue.ideas).Count)." "Continue evidence scoring."
    }

    $active = Read-JsonSafe (Join-Path $moneyDir "active_experiment.json") "active_experiment"
    if ($null -ne $active) {
        Add-Finding "active_experiment" "pass" "low" "Active: $($active.experiment_id) / $($active.idea_id)." "Continue QA."
    }

    $qa = Read-JsonSafe (Join-Path $moneyDir "experiments\exp-0001\qa_checklist.json") "pushbutton_qa"
    if ($null -ne $qa) {
        $collected = @($qa.checks | Where-Object { $_.status -eq "collected" }).Count
        $notChecked = @($qa.checks | Where-Object { $_.status -eq "not_checked" }).Count
        Add-Finding "pushbutton_qa" "info" "low" "Collected=$collected, not_checked=$notChecked." "Next: qa-002 analytics tracking."
    }

    # Internet inbox.
    $inbox = Read-JsonSafe (Join-Path $dataDir "internet_idea_inbox.json") "internet_inbox"
    if ($null -ne $inbox) {
        $ideas = @($inbox.ideas)
        $badXml = @($ideas | Where-Object { $_.evidence_summary -match "System\.Xml\.XmlElement" }).Count
        $weakComments = @($ideas | Where-Object { $_.evidence_summary -eq "Comments" }).Count
        $review = @($ideas | Where-Object { $_.status -eq "source_review_required" }).Count
        $pending = @($ideas | Where-Object { $_.status -eq "evidence_pending" }).Count
        $parked = @($ideas | Where-Object { $_.status -eq "parked_low_signal" }).Count

        Add-Finding "internet_inbox" "info" "low" "Ideas=$($ideas.Count), source_review_required=$review, evidence_pending=$pending, parked=$parked." "Review source-review candidates."

        if ($badXml -gt 0) {
            Add-Finding "internet_inbox" "warn" "medium" "$badXml XML parser summaries remain." "Run internet state repair."
        }
        else {
            Add-Finding "internet_inbox" "pass" "low" "No System.Xml.XmlElement summaries remain." "No action."
        }

        if ($weakComments -gt 0) {
            Add-Finding "internet_inbox" "warn" "medium" "$weakComments ideas have weak summary 'Comments'." "Require source review before promotion."
        }
    }

    # Dedupe registry.
    $registry = Read-JsonSafe (Join-Path $dataDir "internet_seen_registry.json") "internet_dedupe"
    if ($null -ne $registry) {
        $urls = @($registry.seen_urls).Count
        $history = @($registry.history).Count

        if ($urls -gt 0 -and $history -gt 0) {
            Add-Finding "internet_dedupe" "pass" "low" "Registry urls=$urls, history=$history." "No action."
        }
        else {
            Add-Finding "internet_dedupe" "warn" "high" "Registry incomplete: urls=$urls, history=$history." "Backfill registry."
        }
    }


    # BEGIN NOVA MEMORY PACK AUDIT
    Write-AuditLog "Checking Nova local memory pack..."

    $memoryFiles = @(
        [pscustomobject]@{
            area = "memory_pack"
            name = "NOVA_AI_CONTEXT.md"
            path = Join-Path $moneyDir "NOVA_AI_CONTEXT.md"
        },
        [pscustomobject]@{
            area = "memory_pack"
            name = "AUTONOMY_AND_ESCALATION_POLICY.md"
            path = Join-Path $moneyDir "AUTONOMY_AND_ESCALATION_POLICY.md"
        },
        [pscustomobject]@{
            area = "memory_pack"
            name = "BUDGET_ROI_POLICY.md"
            path = Join-Path $moneyDir "BUDGET_ROI_POLICY.md"
        },
        [pscustomobject]@{
            area = "memory_pack"
            name = "DASHBOARD_APPROVAL_MODEL.md"
            path = Join-Path $moneyDir "DASHBOARD_APPROVAL_MODEL.md"
        }
    )

    foreach ($memoryFile in $memoryFiles) {
        if (Test-Path $memoryFile.path) {
            Add-Finding $memoryFile.area "pass" "low" "Found $($memoryFile.name)." "No action."
        }
        else {
            Add-Finding $memoryFile.area "fail" "high" "Missing $($memoryFile.name): $($memoryFile.path)" "Restore or recreate the local memory pack."
        }
    }

    $contextJsonPath = Join-Path $dataDir "nova_ai_context.json"
    $contextJson = Read-JsonSafe $contextJsonPath "memory_pack"

    if ($null -ne $contextJson) {
        Add-Finding "memory_pack" "pass" "low" "nova_ai_context.json parsed successfully." "No action."

        $safety = $contextJson.safety

        $safetyLocked =
            ($safety.external_actions_enabled -eq $false) -and
            ($safety.spending_enabled -eq $false) -and
            ($safety.outreach_enabled -eq $false) -and
            ($safety.publishing_enabled -eq $false)

        if ($safetyLocked) {
            Add-Finding "memory_pack" "pass" "low" "Safety flags are locked: external actions, spending, outreach, and publishing are disabled." "No action."
        }
        else {
            Add-Finding "memory_pack" "fail" "critical" "One or more safety flags are not disabled in nova_ai_context.json." "Stop automation and review nova_ai_context.json immediately."
        }

        if ($contextJson.dashboard.allowed_write_target -match "opportunity_index\.json") {
            Add-Finding "memory_pack" "pass" "low" "Dashboard v1 write target is limited to opportunity_index.json." "No action."
        }
        else {
            Add-Finding "memory_pack" "fail" "high" "Dashboard allowed_write_target is not limited to opportunity_index.json." "Restore dashboard approval model before enabling UI writes."
        }

        if ($contextJson.budget_roi.current_mode -eq "no_real_spending" -and $contextJson.budget_roi.principle -match "ROI") {
            Add-Finding "memory_pack" "pass" "low" "Budget policy is no-real-spending and ROI-based." "No action."
        }
        else {
            Add-Finding "memory_pack" "warn" "medium" "Budget policy is missing expected no-real-spending or ROI language." "Review BUDGET_ROI_POLICY.md and nova_ai_context.json."
        }

        $requiredChrisGates = @(
            "publishing",
            "selling",
            "outreach",
            "sending messages",
            "spending money",
            "using credentials",
            "changing live sites",
            "increasing budget limits"
        )

        $missingGates = @()

        foreach ($gate in $requiredChrisGates) {
            if (@($contextJson.authority_model.chris_required_before) -notcontains $gate) {
                $missingGates += $gate
            }
        }

        if ($missingGates.Count -eq 0) {
            Add-Finding "memory_pack" "pass" "low" "Chris-required authority gates are present." "No action."
        }
        else {
            Add-Finding "memory_pack" "fail" "high" "Missing Chris-required gates: $($missingGates -join ', ')." "Restore authority model before continuing."
        }
    }
    # END NOVA MEMORY PACK AUDIT

    # Source health.
    $sourceHealth = Read-JsonSafe (Join-Path $reportsDir "internet-source-health.json") "source_health"
    if ($null -ne $sourceHealth) {
        Add-Finding "source_health" "pass" "low" "Reachable sources=$($sourceHealth.reachable), total_items=$($sourceHealth.total_items_found)." "Use healthy sources only."
    }

    # V2 report.
    $v2 = Read-JsonSafe (Join-Path $reportsDir "internet-auto-discover-v2-report.json") "auto_discover_v2"
    if ($null -ne $v2) {
        Add-Finding "auto_discover_v2" "pass" "low" "Checked=$($v2.checked_total), added=$($v2.added_total), low_signal=$($v2.skipped_low_signal_total), duplicates=$($v2.skipped_duplicate_total)." "Review added candidates."
    }

    foreach ($scriptName in @(
        "nova-heartbeat.ps1",
        "nova-money-scout-packet.ps1",
        "nova-internet-source-health.ps1",
        "nova-internet-auto-discover-v2.ps1"
    )) {
        if (Test-Path (Join-Path $scriptsDir $scriptName)) {
            Add-Finding "scripts" "pass" "low" "Found $scriptName." "No action."
        }
        else {
            Add-Finding "scripts" "warn" "medium" "Missing $scriptName." "Recreate before scheduling."
        }
    }

    $summary = [pscustomobject]@{
        generated_at = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
        totals = [pscustomobject]@{
            pass = @($findings | Where-Object { $_.status -eq "pass" }).Count
            warn = @($findings | Where-Object { $_.status -eq "warn" }).Count
            fail = @($findings | Where-Object { $_.status -eq "fail" }).Count
            info = @($findings | Where-Object { $_.status -eq "info" }).Count
        }
        findings = $findings
    }

    $summary | ConvertTo-Json -Depth 20 | Set-Content -Path $jsonPath -Encoding UTF8

    $md = @()
    $md += "# Nova Enterprise Audit"
    $md += ""
    $md += "Generated At: $($summary.generated_at)"
    $md += ""
    $md += "## Totals"
    $md += "- Pass: $($summary.totals.pass)"
    $md += "- Warn: $($summary.totals.warn)"
    $md += "- Fail: $($summary.totals.fail)"
    $md += "- Info: $($summary.totals.info)"
    $md += ""
    $md += "## Findings"

    foreach ($f in $findings) {
        $md += ""
        $md += "### [$($f.status.ToUpper())] $($f.area)"
        $md += "- Severity: $($f.severity)"
        $md += "- Detail: $($f.detail)"
        $md += "- Next action: $($f.next_action)"
    }

    $md | Set-Content -Path $reportPath -Encoding UTF8

    Write-AuditLog "Audit complete."
    Get-Content $reportPath -TotalCount 120
}
catch {
    Write-Error "[Nova Enterprise Audit] FAILED: $($_.Exception.Message)"
    exit 1
}

