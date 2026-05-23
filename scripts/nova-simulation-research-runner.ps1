$ErrorActionPreference = "Stop"

function Write-SimLog {
    param([string]$Message, [string]$Level = "INFO")
    Write-Host "[Simulation Research Runner][$Level] $Message"
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

function Get-TextScore {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return 0
    }

    if ($Value.Length -ge 80) {
        return 2
    }

    return 1
}

function Get-RiskScore {
    param($Experiment)

    $title = ([string]$Experiment.title).ToLowerInvariant()
    $risk = 0

    # Higher risk lowers the simulation score.
    foreach ($term in @(
        "sms",
        "outreach",
        "medical",
        "weapon",
        "gun",
        "alcohol",
        "nicotine",
        "crypto",
        "ticket",
        "real estate",
        "vehicle"
    )) {
        if ($title.Contains($term)) {
            $risk += 2
        }
    }

    if ($Experiment.external_action_allowed -eq $true -or $Experiment.real_world_allowed -eq $true) {
        $risk += 10
    }

    return $risk
}

function Get-SimulationScore {
    param($Experiment)

    $score = 0

    # Priority is evidence of what Nova should spend effort on.
    $score += [int]$Experiment.priority_index

    # Artifact-backed ideas get a little boost because they can be improved locally.
    if (-not [string]::IsNullOrWhiteSpace([string]$Experiment.artifact_id)) {
        $score += 2
    }

    # Specific work type improves usefulness.
    if ($Experiment.work_type -eq "artifact_improvement") {
        $score += 2
    }
    elseif ($Experiment.work_type -eq "deeper_local_research") {
        $score += 1
    }

    # A readable hypothesis and tests make the simulation more useful.
    $score += Get-TextScore -Value ([string]$Experiment.hypothesis)
    $score += @($Experiment.simulation_tests).Count

    # Risk reduces score.
    $score -= Get-RiskScore -Experiment $Experiment

    return $score
}

function Get-NextLocalAction {
    param($Experiment, [int]$Score)

    if ($Experiment.item_id -eq "idx-manual-finder-001") {
        return "Run finder-fee category simulation: pick 3 legal hard-to-find item categories, estimate upfront research fee viability, estimate 1 percent success fee value, and reject restricted/platform-risk categories."
    }

    if ($Experiment.work_type -eq "artifact_improvement") {
        return "Improve local artifact quality: clarify buyer pain, strengthen value proposition, identify proof needed, and prepare a stronger review packet."
    }

    if ($Score -ge 8) {
        return "Continue deeper local research and prepare artifact-creation recommendation."
    }

    if ($Score -ge 4) {
        return "Keep researching but require stronger evidence before artifact creation."
    }

    return "Weak simulation signal. Watch only; if repeated weak attempts accumulate, recommend Bury -1."
}

function Get-Recommendation {
    param($Experiment, [int]$Score)

    if ($Experiment.external_action_allowed -eq $true -or $Experiment.real_world_allowed -eq $true) {
        return "stop_due_to_unsafe_permission"
    }

    if ($Score -ge 10) {
        return "continue_and_prepare_stronger_packet"
    }

    if ($Score -ge 6) {
        return "continue_simulation"
    }

    if ($Score -ge 3) {
        return "watch_for_more_evidence"
    }

    return "possible_future_decrement_if_repeated"
}

try {
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $dataDir = Join-Path $workspace "data"
    $reportsDir = Join-Path $workspace "reports"

    $planPath = Join-Path $reportsDir "nova-experiment-plan.json"
    $ledgerPath = Join-Path $dataDir "experiment_ledger.json"
    $jsonOutPath = Join-Path $reportsDir "nova-simulation-research-run.json"
    $mdOutPath = Join-Path $reportsDir "nova-simulation-research-run.md"

    $plan = Read-JsonSafe -Path $planPath -Label "experiment plan"
    $ledger = Read-JsonSafe -Path $ledgerPath -Label "experiment ledger"

    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $runId = "simrun-$stamp"

    $planned = @($plan.planned_experiments | Sort-Object rank | Select-Object -First 5)
    $attempts = @()

    foreach ($experiment in $planned) {
        $score = Get-SimulationScore -Experiment $experiment
        $recommendation = Get-Recommendation -Experiment $experiment -Score $score
        $nextAction = Get-NextLocalAction -Experiment $experiment -Score $score

        $attempts += [pscustomobject]@{
            run_id = $runId
            experiment_id = $experiment.experiment_id
            item_id = $experiment.item_id
            title = $experiment.title
            rank = [int]$experiment.rank
            priority_index = [int]$experiment.priority_index
            mode = "simulation_only"
            simulated_at = $now
            simulation_score = $score
            recommendation = $recommendation
            next_local_action = $nextAction
            measured_revenue_usd = 0
            measured_spend_usd = 0
            measured_roi_percent = 0
            real_world_allowed = $false
            external_action_allowed = $false
            notes = "Local simulation/research pass only. This does not prove demand, revenue, conversion, or ROI."
        }
    }

    $experiments = @($ledger.experiments)

    foreach ($attempt in $attempts) {
        $match = @($experiments | Where-Object { $_.experiment_id -eq $attempt.experiment_id }) | Select-Object -First 1

        if ($null -ne $match) {
            $match.updated_at = $now
            $match.status = "simulation_active"
            $match.outcome = [pscustomobject]@{
                status = $attempt.recommendation
                measured_revenue_usd = 0
                measured_spend_usd = 0
                measured_roi_percent = 0
                notes = $attempt.notes
                last_simulation_score = $attempt.simulation_score
                next_local_action = $attempt.next_local_action
            }

            if ($match.PSObject.Properties.Name -contains "simulation_attempts") {
                $match.simulation_attempts = @($match.simulation_attempts) + $attempt
            }
            else {
                $match | Add-Member -MemberType NoteProperty -Name "simulation_attempts" -Value @($attempt)
            }
        }
    }

    $ledger.updated_at = $now
    $ledger.experiments = $experiments
    $ledger.summary = [pscustomobject]@{
        planned_experiments = @($experiments | Where-Object { $_.status -eq "planned" }).Count
        simulated_attempts = @($experiments | Where-Object { $_.status -eq "simulation_active" }).Count
        real_world_attempts = @($experiments | Where-Object { $_.mode -eq "real_world" }).Count
        winners = @($experiments | Where-Object { $_.outcome.status -eq "winner" }).Count
        exhausted = @($experiments | Where-Object { $_.status -eq "exhausted" }).Count
        recommended_decrements = @($experiments | Where-Object { $_.outcome.status -eq "possible_future_decrement_if_repeated" }).Count
    }

    $ledger | ConvertTo-Json -Depth 60 | Set-Content -Path $ledgerPath -Encoding UTF8

    $run = [pscustomobject]@{
        schema_version = "1.0"
        run_id = $runId
        generated_at = $now
        mode = "simulation_only"
        source_plan = $plan.latest_work_order_id
        attempts = $attempts
        safety = "Simulation/research only. No publishing, selling, outreach, sending messages, commits, pushes, spending, credentials, payment collection, buying, shipping, affiliate changes, or live-site changes."
    }

    $run | ConvertTo-Json -Depth 60 | Set-Content -Path $jsonOutPath -Encoding UTF8

    $md = @()
    $md += "# Nova Simulation Research Run"
    $md += ""
    $md += "- Run ID: $runId"
    $md += "- Generated At: $now"
    $md += "- Mode: simulation_only"
    $md += "- Source Work Order: $($plan.latest_work_order_id)"
    $md += ""
    $md += "## Attempts"

    foreach ($attempt in $attempts) {
        $md += ""
        $md += "### $($attempt.item_id)"
        $md += "- Title: $($attempt.title)"
        $md += "- Rank: $($attempt.rank)"
        $md += "- Priority Index: $($attempt.priority_index)"
        $md += "- Simulation Score: $($attempt.simulation_score)"
        $md += "- Recommendation: $($attempt.recommendation)"
        $md += "- Next Local Action: $($attempt.next_local_action)"
        $md += "- Revenue: `$0"
        $md += "- Spend: `$0"
        $md += "- ROI: 0%"
        $md += "- Real World Allowed: false"
        $md += "- External Action Allowed: false"
    }

    $md += ""
    $md += "## Safety"
    $md += $run.safety

    $md | Set-Content -Path $mdOutPath -Encoding UTF8

    Write-SimLog "Simulation research run complete."
    Write-SimLog "Run report: $mdOutPath"
    Write-SimLog "Run JSON: $jsonOutPath"
    Write-SimLog "Experiment ledger updated: $ledgerPath"
}
catch {
    Write-Error "[Simulation Research Runner] FAILED: $($_.Exception.Message)"
    exit 1
}
