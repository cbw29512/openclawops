$ErrorActionPreference = "Stop"

function Write-FinderLog {
    param([string]$Message, [string]$Level = "INFO")
    Write-Host "[Finder Fee Category Simulation][$Level] $Message"
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
        throw "Invalid JSON in $Label file: $($_.Exception.Message)"
    }
}

function Get-FeeScore {
    param([decimal]$Budget, [decimal]$UpfrontFee)

    $successFee = [math]::Round($Budget * 0.01, 2)
    $totalFee = [math]::Round($UpfrontFee + $successFee, 2)

    if ($totalFee -ge 25) { return 4 }
    if ($totalFee -ge 15) { return 3 }
    if ($totalFee -ge 8) { return 2 }
    return 1
}

function Get-RiskPenalty {
    param([string]$Risk)

    switch ($Risk) {
        "low" { return 0 }
        "medium" { return 1 }
        "high" { return 4 }
        default { return 2 }
    }
}

try {
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $dataDir = Join-Path $workspace "data"
    $reportsDir = Join-Path $workspace "reports"

    $rulesPath = Join-Path $dataDir "finder_fee_concierge_rules.json"
    $jsonOutPath = Join-Path $reportsDir "finder-fee-category-simulation.json"
    $mdOutPath = Join-Path $reportsDir "finder-fee-category-simulation.md"

    $rules = Read-JsonSafe -Path $rulesPath -Label "finder fee rules"

    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $runId = "findercat-$stamp"

    $upfrontFee = [decimal]$rules.pricing_model.suggested_upfront_fee_usd
    $successPercent = [decimal]$rules.pricing_model.success_fee_percent

    $candidates = @(
        [pscustomobject]@{
            category_id = "discontinued-appliance-parts"
            category_name = "Discontinued appliance replacement parts"
            target_buyer = "Homeowners, landlords, and appliance repair techs"
            estimated_item_budget_usd = 250
            category_risk = "low"
            repeatability_score = 4
            request_clarity_score = 4
            notes = "Specific model numbers make requests searchable. Non-regulated. Good fit for research/match packets."
        },
        [pscustomobject]@{
            category_id = "arcade-pinball-parts"
            category_name = "Arcade and pinball machine parts"
            target_buyer = "Collectors, repair hobbyists, and small arcade operators"
            estimated_item_budget_usd = 300
            category_risk = "low"
            repeatability_score = 4
            request_clarity_score = 3
            notes = "Hard-to-find parts, active collector demand, and clear part identifiers make this a promising simulation category."
        },
        [pscustomobject]@{
            category_id = "commercial-kitchen-parts"
            category_name = "Commercial kitchen replacement parts"
            target_buyer = "Small restaurants, food trucks, and equipment repair shops"
            estimated_item_budget_usd = 400
            category_risk = "medium"
            repeatability_score = 3
            request_clarity_score = 4
            notes = "Higher fee potential, but condition/safety fit must be handled carefully before any real-world use."
        },
        [pscustomobject]@{
            category_id = "vintage-audio-components"
            category_name = "Vintage audio components and repair parts"
            target_buyer = "Collectors, repair shops, and audio hobbyists"
            estimated_item_budget_usd = 225
            category_risk = "medium"
            repeatability_score = 3
            request_clarity_score = 3
            notes = "Good collector niche, but authenticity and condition risk require careful match documentation."
        },
        [pscustomobject]@{
            category_id = "industrial-sewing-parts"
            category_name = "Industrial sewing machine parts"
            target_buyer = "Tailors, upholstery shops, and repair techs"
            estimated_item_budget_usd = 275
            category_risk = "low"
            repeatability_score = 3
            request_clarity_score = 4
            notes = "Part numbers and machine models make research practical. Good small-business buyer profile."
        }
    )

    $simulated = @()

    foreach ($candidate in $candidates) {
        $budget = [decimal]$candidate.estimated_item_budget_usd
        $successFee = [math]::Round($budget * ($successPercent / 100), 2)
        $totalFee = [math]::Round($upfrontFee + $successFee, 2)

        $feeScore = Get-FeeScore -Budget $budget -UpfrontFee $upfrontFee
        $riskPenalty = Get-RiskPenalty -Risk $candidate.category_risk
        $score = [int]($feeScore + $candidate.repeatability_score + $candidate.request_clarity_score - $riskPenalty)

        $recommendation = "continue_simulation"
        if ($score -ge 10) {
            $recommendation = "prepare_stronger_match_packet_template"
        }
        elseif ($score -lt 6) {
            $recommendation = "watch_only_until_stronger_signal"
        }

        $simulated += [pscustomobject]@{
            category_id = $candidate.category_id
            category_name = $candidate.category_name
            target_buyer = $candidate.target_buyer
            estimated_item_budget_usd = $budget
            upfront_fee_usd = $upfrontFee
            success_fee_percent = $successPercent
            estimated_success_fee_usd = $successFee
            total_possible_fee_usd = $totalFee
            category_risk = $candidate.category_risk
            simulation_score = $score
            recommendation = $recommendation
            next_local_action = "Create a sample request intake and match-packet checklist for this category. Do not message, buy, sell, collect payment, or post listings."
            notes = $candidate.notes
            measured_revenue_usd = 0
            measured_spend_usd = 0
            measured_roi_percent = 0
            real_world_allowed = $false
            external_action_allowed = $false
        }
    }

    $topCategories = @($simulated | Sort-Object simulation_score -Descending | Select-Object -First 3)

    $result = [pscustomobject]@{
        schema_version = "1.0"
        run_id = $runId
        generated_at = $now
        business_model = "finder_fee_sourcing_concierge"
        mode = "simulation_only"
        pricing_model = $rules.pricing_model
        top_categories = $topCategories
        all_categories = $simulated
        safety = "Local category simulation only. No messaging, buying, selling, collecting payment, posting listings, spending, credentials, shipping, or platform circumvention."
    }

    $result | ConvertTo-Json -Depth 40 | Set-Content -Path $jsonOutPath -Encoding UTF8

    $md = @()
    $md += "# Finder Fee Category Simulation"
    $md += ""
    $md += "- Run ID: $runId"
    $md += "- Generated At: $now"
    $md += "- Mode: simulation_only"
    $md += "- Upfront Fee: `$$upfrontFee"
    $md += "- Success Fee: $successPercent%"
    $md += ""
    $md += "## Top Categories"

    foreach ($cat in $topCategories) {
        $md += ""
        $md += "### $($cat.category_name)"
        $md += "- Category ID: $($cat.category_id)"
        $md += "- Target Buyer: $($cat.target_buyer)"
        $md += "- Estimated Item Budget: `$$($cat.estimated_item_budget_usd)"
        $md += "- Upfront Fee: `$$($cat.upfront_fee_usd)"
        $md += "- Estimated 1% Success Fee: `$$($cat.estimated_success_fee_usd)"
        $md += "- Total Possible Fee: `$$($cat.total_possible_fee_usd)"
        $md += "- Risk: $($cat.category_risk)"
        $md += "- Simulation Score: $($cat.simulation_score)"
        $md += "- Recommendation: $($cat.recommendation)"
        $md += "- Next Local Action: $($cat.next_local_action)"
        $md += "- Real World Allowed: false"
        $md += "- External Action Allowed: false"
    }

    $md += ""
    $md += "## Safety"
    $md += $result.safety

    $md | Set-Content -Path $mdOutPath -Encoding UTF8

    Write-FinderLog "Finder fee category simulation complete."
    Write-FinderLog "Markdown: $mdOutPath"
    Write-FinderLog "JSON: $jsonOutPath"
}
catch {
    Write-Error "[Finder Fee Category Simulation] FAILED: $($_.Exception.Message)"
    exit 1
}
