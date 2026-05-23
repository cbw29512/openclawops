$ErrorActionPreference = "Stop"

function Write-WorkLog {
    param([string]$Message, [string]$Level = "INFO")
    Write-Host "[Nova Work Order][$Level] $Message"
}

function Read-JsonSafe {
    param(
        [Parameter(Mandatory = $true)] [string]$Path,
        [Parameter(Mandatory = $true)] [string]$Label
    )

    # Fail closed: if a required input is missing or invalid, do not invent a work order.
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

function Get-WorkType {
    param($Item)

    # Artifact-backed opportunities should get improvement effort first.
    if (-not [string]::IsNullOrWhiteSpace([string]$Item.artifact_id)) {
        return "artifact_improvement"
    }

    # Priority 2 means Chris gave it a signal but it still needs evidence.
    if ([int]$Item.priority_index -ge 2) {
        return "deeper_local_research"
    }

    return "light_source_watch"
}

function Get-LocalAction {
    param($Item, [string]$WorkType)

    switch ($WorkType) {
        "artifact_improvement" {
            return "Improve the existing local artifact, research adjacent angles, and prepare a stronger review packet. Do not publish or sell."
        }
        "deeper_local_research" {
            return "Gather more local evidence, look for repeated market signals, compare adjacent opportunities, and decide whether artifact creation is justified."
        }
        default {
            return "Watch lightly for new evidence. Do not spend active cycles unless priority or evidence improves."
        }
    }
}

try {
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $reportsDir = Join-Path $workspace "reports"

    $dailyPath = Join-Path $reportsDir "daily-money-report.json"
    $queuePath = Join-Path $reportsDir "source-review-queue.json"
    $jsonOutPath = Join-Path $reportsDir "nova-work-order.json"
    $mdOutPath = Join-Path $reportsDir "nova-work-order.md"

    $daily = Read-JsonSafe -Path $dailyPath -Label "daily money report"
    $queue = Read-JsonSafe -Path $queuePath -Label "source review queue"

    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $workOrderId = "work-$stamp"

    $allItems = @($queue.items)

    # Ranking rule:
    # 1. Positive queue first.
    # 2. Then boosted source-review items with priority >= 2.
    # 3. Then normal active-watch items.
    # 4. Never include idea_pit/deep_freeze as active work.
    $candidateItems = @(
        $allItems |
            Where-Object {
                $_.recommended_dashboard_bucket -ne "idea_pit" -and
                [int]$_.priority_index -gt 0
            } |
            Sort-Object `
                @{ Expression = { if ($_.recommended_dashboard_bucket -eq "positive_queue") { 0 } else { 1 } }; Ascending = $true },
                @{ Expression = { -1 * [int]$_.priority_index }; Ascending = $true },
                @{ Expression = { $_.item_id }; Ascending = $true } |
            Select-Object -First 7
    )

    $workItems = @()
    $rank = 1

    foreach ($item in $candidateItems) {
        $workType = Get-WorkType -Item $item
        $localAction = Get-LocalAction -Item $item -WorkType $workType

        $workItems += [pscustomobject]@{
            rank = $rank
            item_id = $item.item_id
            idea_id = $item.idea_id
            artifact_id = $item.artifact_id
            title = $item.title
            priority_index = [int]$item.priority_index
            dashboard_bucket = $item.recommended_dashboard_bucket
            evidence_quality = $item.evidence_quality
            source_url = $item.source_url
            work_type = $workType
            local_action = $localAction
            why_selected = "Selected by dashboard bucket, priority_index, artifact presence, and Chris Boost/Bury signals."
            external_action_allowed = $false
            blocked_until_chris_approves = @(
                "publishing",
                "selling",
                "outreach",
                "sending messages",
                "committing code",
                "pushing to GitHub",
                "spending money",
                "using credentials",
                "changing affiliate links",
                "changing live sites",
                "claiming legal/compliance certainty"
            )
        }

        $rank += 1
    }

    $workOrder = [pscustomobject]@{
        schema_version = "1.0"
        work_order_id = $workOrderId
        generated_at = $now
        status = "local_only"
        latest_cycle = $daily.latest_cycle
        audit = $daily.audit
        selection_rules = @(
            "active_positive items first",
            "artifact-backed items before raw ideas",
            "priority_index 2+ gets deeper local research",
            "priority_index 1 gets light watch",
            "idea_pit is excluded unless revived",
            "external action is never allowed by work order v1"
        )
        items = $workItems
        safety = "Local work order only. No publishing, selling, outreach, sending messages, commits, pushes, spending, credentials, affiliate changes, or live-site changes."
    }

    $workOrder | ConvertTo-Json -Depth 40 | Set-Content -Path $jsonOutPath -Encoding UTF8

    $md = @()
    $md += "# Nova Work Order"
    $md += ""
    $md += "- Work Order ID: $workOrderId"
    $md += "- Generated At: $now"
    $md += "- Status: local_only"
    $md += "- Latest Cycle: $($daily.latest_cycle.cycle_id)"
    $md += "- Audit Fail: $($daily.audit.fail)"
    $md += ""
    $md += "## Selection Rules"

    foreach ($rule in $workOrder.selection_rules) {
        $md += "- $rule"
    }

    $md += ""
    $md += "## Work Items"

    foreach ($item in $workItems) {
        $md += ""
        $md += "### $($item.rank). $($item.item_id)"
        $md += "- Title: $($item.title)"
        $md += "- Priority Index: $($item.priority_index)"
        $md += "- Bucket: $($item.dashboard_bucket)"
        $md += "- Evidence Quality: $($item.evidence_quality)"
        $md += "- Artifact: $($item.artifact_id)"
        $md += "- Work Type: $($item.work_type)"
        $md += "- Local Action: $($item.local_action)"
        $md += "- Source URL: $($item.source_url)"
        $md += "- External Action Allowed: false"
    }

    $md += ""
    $md += "## Safety"
    $md += $workOrder.safety

    $md | Set-Content -Path $mdOutPath -Encoding UTF8

    Write-WorkLog "Work order created."
    Write-WorkLog "Markdown: $mdOutPath"
    Write-WorkLog "JSON: $jsonOutPath"
}
catch {
    Write-Error "[Nova Work Order] FAILED: $($_.Exception.Message)"
    exit 1
}
