$ErrorActionPreference = "Stop"

function Write-ManifestLog {
    param([string]$Message, [string]$Level = "INFO")
    Write-Host "[System Manifest][$Level] $Message"
}

function Test-PathStatus {
    param([string]$Path)

    return [pscustomobject]@{
        path = $Path
        exists = Test-Path $Path
    }
}

try {
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $dataDir = Join-Path $workspace "data"
    $scriptsDir = Join-Path $workspace "scripts"
    $reportsDir = Join-Path $workspace "reports"
    $moneyDir = Join-Path $workspace "money_scout"

    New-Item -ItemType Directory -Force -Path $dataDir, $reportsDir | Out-Null

    $manifestPath = Join-Path $dataDir "system_manifest.json"
    $reportPath = Join-Path $reportsDir "system-manifest-report.md"

    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

    $requiredScripts = @(
        "nova-ops-cycle.ps1",
        "nova-activity-log.ps1",
        "nova-enterprise-audit.ps1",
        "nova-internet-source-health.ps1",
        "nova-internet-auto-discover-v2.ps1",
        "nova-weak-summary-repair.ps1",
        "nova-opportunity-index-init.ps1",
        "nova-source-review-queue.ps1",
        "nova-artifact-factory.ps1",
        "nova-daily-money-report.ps1",
        "nova-work-order.ps1",
        "nova-experiment-plan.ps1",
        "nova-simulation-research-runner.ps1",
        "nova-finder-fee-category-simulation.ps1",
        "nova-learning-ledger-init.ps1"
    )

    $requiredData = @(
        "internet_idea_inbox.json",
        "internet_seen_registry.json",
        "artifact_registry.json",
        "opportunity_index.json",
        "nova_ai_context.json",
        "learning_ledger.json",
        "experiment_ledger.json",
        "finder_fee_concierge_rules.json"
    )

    $requiredPolicies = @(
        "NOVA_AI_CONTEXT.md",
        "AUTONOMY_AND_ESCALATION_POLICY.md",
        "BUDGET_ROI_POLICY.md",
        "DASHBOARD_APPROVAL_MODEL.md",
        "LEARNING_LOOP_POLICY.md",
        "REPLICATION_POLICY.md",
        "EXPERIMENT_LOOP_POLICY.md",
        "FINDER_FEE_CONCIERGE_POLICY.md"
    )

    $scriptStatus = @()
    foreach ($script in $requiredScripts) {
        $scriptStatus += Test-PathStatus -Path (Join-Path $scriptsDir $script)
    }

    $dataStatus = @()
    foreach ($data in $requiredData) {
        $dataStatus += Test-PathStatus -Path (Join-Path $dataDir $data)
    }

    $policyStatus = @()
    foreach ($policy in $requiredPolicies) {
        $policyStatus += Test-PathStatus -Path (Join-Path $moneyDir $policy)
    }

    $manifest = [pscustomobject]@{
        schema_version = "1.0"
        generated_at = $now
        workspace = $workspace
        scheduled_task = "Nova Money Scout Ops Cycle"
        local_only = $true
        external_actions_enabled = $false
        spending_enabled = $false
        outreach_enabled = $false
        publishing_enabled = $false
        required_scripts = $scriptStatus
        required_data = $dataStatus
        required_policies = $policyStatus
        replication_warning = "Do not copy credentials, API keys, payment methods, browser sessions, cookies, account tokens, affiliate credentials, email sending credentials, or deployment secrets."
    }

    $manifest | ConvertTo-Json -Depth 30 | Set-Content -Path $manifestPath -Encoding UTF8

    $missingCount =
        @($scriptStatus | Where-Object { -not $_.exists }).Count +
        @($dataStatus | Where-Object { -not $_.exists }).Count +
        @($policyStatus | Where-Object { -not $_.exists }).Count

    $md = @()
    $md += "# System Manifest Report"
    $md += ""
    $md += "Generated At: $now"
    $md += ""
    $md += "## Summary"
    $md += "- Workspace: $workspace"
    $md += "- Scheduled Task: Nova Money Scout Ops Cycle"
    $md += "- Missing Required Items: $missingCount"
    $md += "- Local Only: true"
    $md += "- External Actions Enabled: false"
    $md += "- Spending Enabled: false"
    $md += "- Outreach Enabled: false"
    $md += "- Publishing Enabled: false"
    $md += ""
    $md += "## Required Scripts"

    foreach ($item in $scriptStatus) {
        $md += "- [$($item.exists)] $($item.path)"
    }

    $md += ""
    $md += "## Required Data"

    foreach ($item in $dataStatus) {
        $md += "- [$($item.exists)] $($item.path)"
    }

    $md += ""
    $md += "## Required Policies"

    foreach ($item in $policyStatus) {
        $md += "- [$($item.exists)] $($item.path)"
    }

    $md += ""
    $md += "## Replication Warning"
    $md += $manifest.replication_warning

    $md | Set-Content -Path $reportPath -Encoding UTF8

    Write-ManifestLog "System manifest updated."
    Write-ManifestLog "Manifest: $manifestPath"
    Write-ManifestLog "Report: $reportPath"
}
catch {
    Write-Error "[System Manifest] FAILED: $($_.Exception.Message)"
    exit 1
}






