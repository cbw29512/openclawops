$ErrorActionPreference = "Stop"

function Write-ExperimentLog {
    param([string]$Message, [string]$Level = "INFO")
    Write-Host "[Nova Experiment Plan][$Level] $Message"
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

function Get-SimulationTests {
    param($Item)

    $tests = @()

    if ($Item.work_type -eq "artifact_improvement") {
        $tests += "Review existing artifact for clarity, usefulness, and buyer pain alignment."
        $tests += "Identify 3 adjacent monetizable angles without publishing anything."
        $tests += "Draft a stronger local-only value proposition."
        $tests += "List proof required before this can become a real offer."
    }
    elseif ($Item.work_type -eq "deeper_local_research") {
        $tests += "Search local records for repeated signals around this pain point."
        $tests += "Compare the idea against current positive queue themes."
        $tests += "Draft a simulated offer and define who would pay."
        $tests += "Score whether artifact creation is justified."
    }
    else {
        $tests += "Watch for stronger evidence before active work."
        $tests += "Define what new signal would justify deeper research."
    }

    return $tests
}

function Get-SuccessCriteria {
    param($Item)

    return @(
        "Clear pain point identified",
        "Audience is specific",
        "At least one plausible monetization path exists",
        "Risks are documented",
        "Next local action is obvious",
        "No real-world action required"
    )
}

function Get-FailureCriteria {
    param($Item)

    return @(
        "Pain point remains vague",
        "No specific buyer or user is identified",
        "No artifact or offer path is obvious",
        "Evidence remains title-only or weak",
        "Risk is too high for current safety policy",
        "The idea requires outreach, spending, publishing, or credentials before local validation"
    )
}

try {
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $dataDir = Join-Path $workspace "data"
    $reportsDir = Join-Path $workspace "reports"

    $workOrderPath = Join-Path $reportsDir "nova-work-order.json"
    $ledgerPath = Join-Path $dataDir "experiment_ledger.json"
    $jsonOutPath = Join-Path $reportsDir "nova-experiment-plan.json"
    $mdOutPath = Join-Path $reportsDir "nova-experiment-plan.md"

    $workOrder = Read-JsonSafe -Path $workOrderPath -Label "Nova work order"

    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"

    if (Test-Path $ledgerPath) {
        Copy-Item $ledgerPath "$ledgerPath.bak-$(Get-Date -Format yyyyMMdd-HHmmss)"
        $ledger = Read-JsonSafe -Path $ledgerPath -Label "experiment ledger"
    }
    else {
        $ledger = [pscustomobject]@{
            schema_version = "1.0"
            created_at = $now
            updated_at = $now
            mode = "simulation_first"
            summary = [pscustomobject]@{
                planned_experiments = 0
                simulated_attempts = 0
                real_world_attempts = 0
                winners = 0
                exhausted = 0
                recommended_decrements = 0
            }
            experiments = @()
        }
    }

    $experiments = @($ledger.experiments)
    $planned = @()

    $rankedItems = @($workOrder.items | Sort-Object rank | Select-Object -First 5)

    foreach ($item in $rankedItems) {
        $existing = @($experiments | Where-Object {
            $_.item_id -eq $item.item_id -and
            $_.status -in @("planned", "simulation_active", "needs_review")
        }) | Select-Object -First 1

        if ($null -ne $existing) {
            $planned += $existing
            continue
        }

        $experiment = [pscustomobject]@{
            experiment_id = "exp-$($item.item_id)-$stamp"
            item_id = $item.item_id
            idea_id = $item.idea_id
            artifact_id = $item.artifact_id
            title = $item.title
            rank = [int]$item.rank
            priority_index = [int]$item.priority_index
            mode = "simulation_only"
            status = "planned"
            attempt_number = 1
            created_at = $now
            updated_at = $now
            hypothesis = "This ranked opportunity may produce a useful local artifact, offer, or repeatable money-making process if evidence supports it."
            work_type = $item.work_type
            simulation_tests = Get-SimulationTests -Item $item
            success_criteria = Get-SuccessCriteria -Item $item
            failure_criteria = Get-FailureCriteria -Item $item
            next_simulation_action = "Run local simulation review. Do not perform real-world action."
            real_world_allowed = $false
            external_action_allowed = $false
            outcome = [pscustomobject]@{
                status = "not_run"
                measured_revenue_usd = 0
                measured_spend_usd = 0
                measured_roi_percent = 0
                notes = ""
            }
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

        $experiments += $experiment
        $planned += $experiment
    }

    $ledger.updated_at = $now
    $ledger.experiments = $experiments
    $ledger.summary = [pscustomobject]@{
        planned_experiments = @($experiments | Where-Object { $_.status -eq "planned" }).Count
        simulated_attempts = @($experiments | Where-Object { $_.mode -eq "simulation_only" -and $_.outcome.status -ne "not_run" }).Count
        real_world_attempts = @($experiments | Where-Object { $_.mode -eq "real_world" }).Count
        winners = @($experiments | Where-Object { $_.outcome.status -eq "winner" }).Count
        exhausted = @($experiments | Where-Object { $_.status -eq "exhausted" }).Count
        recommended_decrements = @($experiments | Where-Object { $_.outcome.status -eq "recommend_decrement" }).Count
    }

    $ledger | ConvertTo-Json -Depth 50 | Set-Content -Path $ledgerPath -Encoding UTF8

    $plan = [pscustomobject]@{
        schema_version = "1.0"
        generated_at = $now
        mode = "simulation_first"
        latest_work_order_id = $workOrder.work_order_id
        latest_cycle = $workOrder.latest_cycle
        planned_experiments = $planned
        safety = "Simulation only. No publishing, selling, outreach, sending messages, commits, pushes, spending, credentials, affiliate changes, or live-site changes."
    }

    $plan | ConvertTo-Json -Depth 50 | Set-Content -Path $jsonOutPath -Encoding UTF8

    $md = @()
    $md += "# Nova Experiment Plan"
    $md += ""
    $md += "- Generated At: $now"
    $md += "- Mode: simulation_first"
    $md += "- Work Order: $($workOrder.work_order_id)"
    $md += "- Latest Cycle: $($workOrder.latest_cycle.cycle_id)"
    $md += ""
    $md += "## Planned Simulation Experiments"

    foreach ($experiment in $planned) {
        $md += ""
        $md += "### $($experiment.experiment_id)"
        $md += "- Item: $($experiment.item_id)"
        $md += "- Rank: $($experiment.rank)"
        $md += "- Title: $($experiment.title)"
        $md += "- Priority Index: $($experiment.priority_index)"
        $md += "- Mode: $($experiment.mode)"
        $md += "- Status: $($experiment.status)"
        $md += "- Work Type: $($experiment.work_type)"
        $md += "- Real World Allowed: false"
        $md += "- External Action Allowed: false"
        $md += ""
        $md += "#### Simulation Tests"
        foreach ($test in @($experiment.simulation_tests)) {
            $md += "- $test"
        }
        $md += ""
        $md += "#### Success Criteria"
        foreach ($criterion in @($experiment.success_criteria)) {
            $md += "- $criterion"
        }
        $md += ""
        $md += "#### Failure Criteria"
        foreach ($criterion in @($experiment.failure_criteria)) {
            $md += "- $criterion"
        }
    }

    $md += ""
    $md += "## Safety"
    $md += $plan.safety

    $md | Set-Content -Path $mdOutPath -Encoding UTF8

    Write-ExperimentLog "Experiment plan created."
    Write-ExperimentLog "Ledger: $ledgerPath"
    Write-ExperimentLog "Markdown: $mdOutPath"
    Write-ExperimentLog "JSON: $jsonOutPath"
}
catch {
    Write-Error "[Nova Experiment Plan] FAILED: $($_.Exception.Message)"
    exit 1
}
