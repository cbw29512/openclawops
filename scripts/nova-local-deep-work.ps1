$ErrorActionPreference = "Stop"

function Write-DeepLog {
    param([string]$Message, [string]$Level = "INFO")
    Write-Host "[Nova Local Deep Work][$Level] $Message"
}

function Read-JsonSafe {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return $null
    }

    try {
        return Get-Content $Path -Raw | ConvertFrom-Json
    }
    catch {
        Write-DeepLog "Invalid JSON skipped: $Path :: $($_.Exception.Message)" "WARN"
        return $null
    }
}

function Add-Activity {
    param(
        [string]$EventType,
        [string]$Level,
        [string]$Message,
        [string]$StepName,
        $Details
    )

    try {
        $activityScript = Join-Path $script:scriptsDir "nova-activity-log.ps1"

        if (-not (Test-Path $activityScript)) {
            return
        }

        $json = $Details | ConvertTo-Json -Depth 12 -Compress
        $base64 = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($json))

        powershell -NoProfile -ExecutionPolicy Bypass -File $activityScript `
            -Source "nova-local-deep-work" `
            -EventType $EventType `
            -Level $Level `
            -Message $Message `
            -CycleId $script:runId `
            -StepName $StepName `
            -DetailsBase64 $base64 | Out-Null
    }
    catch {
        Write-DeepLog "Activity log failed: $($_.Exception.Message)" "WARN"
    }
}

function New-MatchPacket {
    param(
        $Category,
        [string]$OutputDir,
        [string]$RunId,
        [string]$Now
    )

    $categoryId = [string]$Category.category_id
    $categoryName = [string]$Category.category_name

    if ([string]::IsNullOrWhiteSpace($categoryId)) {
        return $null
    }

    $safeName = $categoryId -replace '[^a-zA-Z0-9\-_]', '-'
    $path = Join-Path $OutputDir "$safeName-match-packet.md"

    $content = @"
# Finder Fee Match Packet Template: $categoryName

Generated At: $Now  
Run ID: $RunId  
Mode: local_only / simulation_only

## Category Snapshot

- Category ID: $categoryId
- Target Buyer: $($Category.target_buyer)
- Estimated Item Budget: `$$($Category.estimated_item_budget_usd)
- Upfront Research Fee: `$$($Category.upfront_fee_usd)
- Success Fee: $($Category.success_fee_percent)%
- Estimated Success Fee: `$$($Category.estimated_success_fee_usd)
- Total Possible Fee: `$$($Category.total_possible_fee_usd)
- Risk: $($Category.category_risk)
- Simulation Score: $($Category.simulation_score)

## Buyer Intake Checklist

- Exact item name:
- Model number / part number:
- Compatible machine/device/system:
- Acceptable condition:
- Target budget:
- Location or shipping scope:
- Deadline:
- Why buyer cannot easily find this:
- Must-have requirements:
- Deal-breakers:

## Seller / Source Verification Checklist

- Source URL:
- Seller name or business:
- Item photos present:
- Part/model number visible:
- Condition described:
- Return/refund terms visible:
- Shipping/pickup terms visible:
- Red flags:
- Additional verification needed:

## Match Quality Score

- Item specificity: /5
- Seller credibility: /5
- Price fit: /5
- Urgency fit: /5
- Fraud/platform risk: /5
- Overall recommendation:

## Fee Disclosure Draft

This service charges a small upfront research fee before searching begins.  
If a successful buyer/seller match results in a completed transaction, a 1% success fee may apply.  
Nova/Chris does not own the item, guarantee condition, provide escrow, ship the item, or bypass marketplace rules.

## Blocked Actions

Nova may not:

- message buyers
- message sellers
- collect payment
- buy items
- ship items
- post listings
- move marketplace users off-platform
- use credentials
- spend money

## Next Local-Only Research

- Find 3 example request patterns for this category.
- Identify common part-number formats.
- List trusted public research sources.
- Build a stronger intake form draft.
"@

    Set-Content -Path $path -Value $content -Encoding UTF8

    return [pscustomobject]@{
        category_id = $categoryId
        category_name = $categoryName
        path = $path
    }
}

try {
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $script:scriptsDir = Join-Path $workspace "scripts"
    $reportsDir = Join-Path $workspace "reports"
    $packetDir = Join-Path $reportsDir "finder-fee-match-packets"

    New-Item -ItemType Directory -Force -Path $reportsDir, $packetDir | Out-Null

    $script:runId = "deepwork-$(Get-Date -Format yyyyMMdd-HHmmss)"
    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

    Add-Activity -EventType "local_deep_work_started" -Level "INFO" -StepName "local_deep_work" -Message "Local deep work started." -Details @{ started_at = $now }

    $finderPath = Join-Path $reportsDir "finder-fee-category-simulation.json"
    $workOrderPath = Join-Path $reportsDir "nova-work-order.json"

    $finder = Read-JsonSafe -Path $finderPath
    $workOrder = Read-JsonSafe -Path $workOrderPath

    $packets = @()

    foreach ($cat in @($finder.top_categories)) {
        $packet = New-MatchPacket -Category $cat -OutputDir $packetDir -RunId $script:runId -Now $now

        if ($null -ne $packet) {
            $packets += $packet
            Add-Activity -EventType "match_packet_updated" -Level "PASS" -StepName "match_packet" -Message "Updated match packet: $($packet.category_name)" -Details $packet
        }
    }

    $topWork = @($workOrder.items | Select-Object -First 3)

    $result = [pscustomobject]@{
        schema_version = "1.0"
        run_id = $script:runId
        generated_at = $now
        mode = "local_only"
        match_packets_created = @($packets).Count
        match_packets = $packets
        top_work_items = $topWork
        safety = [pscustomobject]@{
            external_action_allowed = $false
            spending_allowed = $false
            outreach_allowed = $false
            publishing_allowed = $false
        }
    }

    $jsonOut = Join-Path $reportsDir "nova-local-deep-work.json"
    $mdOut = Join-Path $reportsDir "nova-local-deep-work.md"

    $result | ConvertTo-Json -Depth 30 | Set-Content -Path $jsonOut -Encoding UTF8

    $md = @()
    $md += "# Nova Local Deep Work"
    $md += ""
    $md += "- Run ID: $script:runId"
    $md += "- Generated At: $now"
    $md += "- Mode: local_only"
    $md += "- Match Packets Created: $(@($packets).Count)"
    $md += ""
    $md += "## Match Packets"

    foreach ($packet in $packets) {
        $md += ""
        $md += "### $($packet.category_name)"
        $md += "- Category ID: $($packet.category_id)"
        $md += "- File: $($packet.path)"
    }

    $md += ""
    $md += "## Safety"
    $md += "No external actions, spending, outreach, publishing, buying, selling, posting, payment collection, shipping, credentials, commits, or pushes."

    $md | Set-Content -Path $mdOut -Encoding UTF8

    Add-Activity -EventType "local_deep_work_completed" -Level "PASS" -StepName "local_deep_work" -Message "Local deep work completed. Match packets updated: $(@($packets).Count)" -Details @{ packets = @($packets).Count; report = $mdOut }

    Write-DeepLog "Local deep work complete."
    Write-DeepLog "Report: $mdOut"
}
catch {
    Add-Activity -EventType "local_deep_work_failed" -Level "FAIL" -StepName "local_deep_work" -Message $_.Exception.Message -Details @{ error = $_.Exception.Message }
    Write-Error "[Nova Local Deep Work] FAILED: $($_.Exception.Message)"
    exit 1
}
