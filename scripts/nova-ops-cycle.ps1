$ErrorActionPreference = "Stop"

function Write-CycleLog {
    param([string]$Message, [string]$Level = "INFO")
    Write-Host "[Nova Ops Cycle][$Level] $Message"
}

function Convert-DetailsToBase64 {
    param([string]$Json)

    try {
        if ([string]::IsNullOrWhiteSpace($Json)) {
            $Json = "{}"
        }

        return [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($Json))
    }
    catch {
        return [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes("{}"))
    }
}

function Add-Activity {
    param(
        [string]$EventType,
        [string]$Level,
        [string]$Message,
        [string]$StepName = "",
        [string]$DetailsJson = "{}"
    )

    try {
        $activityScript = Join-Path $script:ScriptsDir "nova-activity-log.ps1"

        if (Test-Path $activityScript) {
            $detailsBase64 = Convert-DetailsToBase64 -Json $DetailsJson

            powershell -NoProfile -ExecutionPolicy Bypass -File $activityScript `
                -Source "nova-ops-cycle" `
                -EventType $EventType `
                -Level $Level `
                -Message $Message `
                -CycleId $script:CycleId `
                -StepName $StepName `
                -DetailsBase64 $detailsBase64 | Out-Null
        }
    }
    catch {
        # Activity logging should never stop the safe ops cycle.
        Write-CycleLog "Activity logging failed: $($_.Exception.Message)" "WARN"
    }
}

function Invoke-NovaStep {
    param(
        [Parameter(Mandatory = $true)] [pscustomobject]$Step
    )

    $name = [string]$Step.name
    $path = [string]$Step.path
    $logPath = Join-Path $script:StepLogDir "$script:CycleId-$name.log"

    Write-CycleLog "Running $name"
    Add-Activity -EventType "step_started" -Level "INFO" -StepName $name -Message "Running $name" -DetailsJson "{}"

    if (-not (Test-Path $path)) {
        $message = "Missing step script: $path"
        $message | Set-Content -Path $logPath -Encoding UTF8

        Add-Activity -EventType "step_failed" -Level "FAIL" -StepName $name -Message $message -DetailsJson (@{ path = $path } | ConvertTo-Json -Compress)

        return [pscustomobject]@{
            name = $name
            status = "fail"
            exit_code = 1
            detail = $message
            log = $logPath
        }
    }

    try {
        # Capture both stdout and stderr so the step log is a useful proof artifact.
        $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $path *>&1
        $exitCode = $LASTEXITCODE

        if ($null -eq $exitCode) {
            $exitCode = 0
        }

        $output | Out-String | Set-Content -Path $logPath -Encoding UTF8

        if ($exitCode -eq 0) {
            Add-Activity -EventType "step_passed" -Level "PASS" -StepName $name -Message "$name completed" -DetailsJson (@{ exit_code = $exitCode; log = $logPath } | ConvertTo-Json -Compress)

            return [pscustomobject]@{
                name = $name
                status = "pass"
                exit_code = $exitCode
                detail = "Completed"
                log = $logPath
            }
        }

        Add-Activity -EventType "step_failed" -Level "FAIL" -StepName $name -Message "$name failed with exit code $exitCode" -DetailsJson (@{ exit_code = $exitCode; log = $logPath } | ConvertTo-Json -Compress)

        return [pscustomobject]@{
            name = $name
            status = "fail"
            exit_code = $exitCode
            detail = "Failed"
            log = $logPath
        }
    }
    catch {
        $errorMessage = $_.Exception.Message
        $errorMessage | Set-Content -Path $logPath -Encoding UTF8

        Add-Activity -EventType "step_failed" -Level "FAIL" -StepName $name -Message "$name crashed: $errorMessage" -DetailsJson (@{ error = $errorMessage; log = $logPath } | ConvertTo-Json -Compress)

        return [pscustomobject]@{
            name = $name
            status = "fail"
            exit_code = 1
            detail = $errorMessage
            log = $logPath
        }
    }
}

function Write-CycleReports {
    param(
        [array]$Results,
        [string]$Status,
        [string]$GeneratedAt
    )

    $jsonPath = Join-Path $script:CycleDir "latest-cycle.json"
    $mdPath = Join-Path $script:CycleDir "latest-cycle.md"

    $report = [pscustomobject]@{
        schema_version = "1.0"
        cycle_id = $script:CycleId
        status = $Status
        generated_at = $GeneratedAt
        steps = $Results
        safety = "Local reports and local JSON only. No publishing, selling, outreach, commits, pushes, spending, account creation, credential use, affiliate changes, or live site changes."
    }

    $report | ConvertTo-Json -Depth 30 | Set-Content -Path $jsonPath -Encoding UTF8

    $md = @()
    $md += "# Nova Ops Cycle"
    $md += ""
    $md += "- Cycle ID: $script:CycleId"
    $md += "- Status: $Status"
    $md += "- Generated: $GeneratedAt"
    $md += ""
    $md += "## Steps"

    foreach ($result in $Results) {
        $md += ""
        $md += "### $($result.name)"
        $md += "- Status: $($result.status)"
        $md += "- Exit code: $($result.exit_code)"
        $md += "- Detail: $($result.detail)"
        $md += "- Log: $($result.log)"
    }

    $md += ""
    $md += "## Safety"
    $md += $report.safety

    $md | Set-Content -Path $mdPath -Encoding UTF8
}

try {
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $script:ScriptsDir = Join-Path $workspace "scripts"
    $reportsDir = Join-Path $workspace "reports"
    $script:CycleDir = Join-Path $reportsDir "ops-cycle"
    $script:StepLogDir = Join-Path $script:CycleDir "step-logs"

    New-Item -ItemType Directory -Force -Path $script:CycleDir, $script:StepLogDir | Out-Null

    $script:CycleId = "ops-$(Get-Date -Format yyyyMMdd-HHmmss)"
    $startedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

    Write-CycleLog "Starting cycle $script:CycleId"
    Add-Activity -EventType "cycle_started" -Level "INFO" -Message "Starting cycle $script:CycleId" -DetailsJson (@{ started_at = $startedAt } | ConvertTo-Json -Compress)

    # State-first step order. Each step is local-only.
    $steps = @(
        [pscustomobject]@{ name = "source_health"; path = Join-Path $script:ScriptsDir "nova-internet-source-health.ps1" },
        [pscustomobject]@{ name = "auto_discover_v2"; path = Join-Path $script:ScriptsDir "nova-internet-auto-discover-v2.ps1" },
        [pscustomobject]@{ name = "weak_summary_repair"; path = Join-Path $script:ScriptsDir "nova-weak-summary-repair.ps1" },
        [pscustomobject]@{ name = "opportunity_index_init"; path = Join-Path $script:ScriptsDir "nova-opportunity-index-init.ps1" },
        [pscustomobject]@{ name = "source_review_queue"; path = Join-Path $script:ScriptsDir "nova-source-review-queue.ps1" },
        [pscustomobject]@{ name = "artifact_factory"; path = Join-Path $script:ScriptsDir "nova-artifact-factory.ps1" },
        [pscustomobject]@{ name = "enterprise_audit"; path = Join-Path $script:ScriptsDir "nova-enterprise-audit.ps1" },
        [pscustomobject]@{ name = "daily_money_report"; path = Join-Path $script:ScriptsDir "nova-daily-money-report.ps1" },
        [pscustomobject]@{ name = "work_order"; path = Join-Path $script:ScriptsDir "nova-work-order.ps1" },
        [pscustomobject]@{ name = "experiment_plan"; path = Join-Path $script:ScriptsDir "nova-experiment-plan.ps1" },
        [pscustomobject]@{ name = "simulation_research_runner"; path = Join-Path $script:ScriptsDir "nova-simulation-research-runner.ps1" },
        [pscustomobject]@{ name = "finder_fee_category_simulation"; path = Join-Path $script:ScriptsDir "nova-finder-fee-category-simulation.ps1" },
        [pscustomobject]@{ name = "learning_ledger"; path = Join-Path $script:ScriptsDir "nova-learning-ledger-init.ps1" },
        [pscustomobject]@{ name = "system_manifest"; path = Join-Path $script:ScriptsDir "nova-system-manifest.ps1" }
    )

    $results = @()

    foreach ($step in $steps) {
        $results += Invoke-NovaStep -Step $step
    }

    $failed = @($results | Where-Object { $_.status -ne "pass" })
    $status = "pass"

    if ($failed.Count -gt 0) {
        $status = "fail"
    }

    $generatedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

    Write-CycleReports -Results $results -Status $status -GeneratedAt $generatedAt

    Add-Activity -EventType "cycle_complete" -Level ($(if ($status -eq "pass") { "PASS" } else { "FAIL" })) -Message "Cycle $script:CycleId complete: $status" -DetailsJson (@{ status = $status; failed_steps = $failed.Count; generated_at = $generatedAt } | ConvertTo-Json -Compress)

    Write-CycleLog "Cycle complete: $status"
    Write-CycleLog "Latest report: $(Join-Path $script:CycleDir 'latest-cycle.md')"

    if ($status -ne "pass") {
        exit 1
    }

    exit 0
}
catch {
    $message = $_.Exception.Message
    Write-CycleLog "FAILED: $message" "ERROR"

    try {
        Add-Activity -EventType "cycle_crashed" -Level "FAIL" -Message $message -DetailsJson (@{ error = $message } | ConvertTo-Json -Compress)
    }
    catch {}

    exit 1
}

