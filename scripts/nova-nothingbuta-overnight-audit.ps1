try {
    $ErrorActionPreference = "Stop"

    # -----------------------------
    # Objective:
    # Audit the NothingButA local factory after overnight automation.
    #
    # This does NOT commit, push, publish, change GitHub Pages,
    # add analytics, ads, affiliate links, or lead capture.
    # -----------------------------

    $Root = "C:\Users\dmchris\OpenClawOps"
    $DataDir = Join-Path $Root "data"
    $ReportsDir = Join-Path $Root "reports"
    $ScriptsDir = Join-Path $Root "scripts"
    $CandidatesDir = Join-Path $Root "nothingbuta\factory\candidates"

    $TaskName = "NothingButA Local Factory Loop"

    $LatestFactoryJsonPath = Join-Path $ReportsDir "nothingbuta-latest-factory-loop.json"
    $BacklogPath = Join-Path $DataDir "nothingbuta_tool_backlog.json"
    $RegistryPath = Join-Path $DataDir "nothingbuta_candidate_registry.json"
    $FactoryPyPath = Join-Path $ScriptsDir "nova_nothingbuta_local_factory_loop.py"

    $AuditJsonPath = Join-Path $ReportsDir "nothingbuta-overnight-factory-audit.json"
    $AuditMdPath = Join-Path $ReportsDir "nothingbuta-overnight-factory-audit.md"

    function Write-CleanText {
        param(
            [Parameter(Mandatory = $true)][string]$Path,
            [Parameter(Mandatory = $true)][string]$Value
        )

        try {
            $Parent = Split-Path $Path

            if (-not (Test-Path $Parent)) {
                New-Item -ItemType Directory -Path $Parent -Force | Out-Null
            }

            $Encoding = New-Object System.Text.UTF8Encoding($false)
            [System.IO.File]::WriteAllText($Path, $Value, $Encoding)
        }
        catch {
            throw "Failed writing file $Path : $($_.Exception.Message)"
        }
    }

    foreach ($Path in @($LatestFactoryJsonPath, $BacklogPath, $RegistryPath, $FactoryPyPath)) {
        if (-not (Test-Path $Path)) {
            throw "Missing required audit artifact: $Path"
        }
    }

    $Problems = New-Object System.Collections.Generic.List[string]

    # -----------------------------
    # 1. Scheduled task health.
    # -----------------------------

    $TaskInfo = Get-ScheduledTaskInfo -TaskName $TaskName

    if ($TaskInfo.LastTaskResult -ne 0) {
        $Problems.Add("Scheduled task LastTaskResult is not 0: $($TaskInfo.LastTaskResult)")
    }

    if ($TaskInfo.NumberOfMissedRuns -gt 0) {
        $Problems.Add("Scheduled task missed runs: $($TaskInfo.NumberOfMissedRuns)")
    }

    $MinutesSinceLastRun = [math]::Round(((Get-Date) - $TaskInfo.LastRunTime).TotalMinutes, 2)

    if ($MinutesSinceLastRun -gt 30) {
        $Problems.Add("Factory loop has not run in more than 30 minutes. Minutes since last run: $MinutesSinceLastRun")
    }

    # -----------------------------
    # 2. Latest factory run.
    # -----------------------------

    $LatestFactory = Get-Content $LatestFactoryJsonPath -Raw | ConvertFrom-Json

    if ($LatestFactory.status -ne "pass") {
        $Problems.Add("Latest factory status is not pass: $($LatestFactory.status)")
    }

    foreach ($Gate in @("commit_allowed", "push_allowed", "publish_allowed", "external_action_allowed")) {
        if ($LatestFactory.$Gate -ne $false) {
            $Problems.Add("Safety failure: latest factory $Gate is not false.")
        }
    }

    # -----------------------------
    # 3. Candidate counts.
    # -----------------------------

    $Backlog = Get-Content $BacklogPath -Raw | ConvertFrom-Json
    $Registry = Get-Content $RegistryPath -Raw | ConvertFrom-Json

    $Candidates = @($Backlog.candidate_tools)
    $Generated = @($Registry.generated_candidates)

    $Ready = @($Candidates | Where-Object {
        $_.state -eq "local_preview_ready" -and [int]$_.strict_quality_score -eq 100
    })

    $RendererNeeded = @($Candidates | Where-Object {
        $_.state -eq "template_required"
    })

    $RepairNeeded = @($Candidates | Where-Object {
        $_.state -in @("quality_failed", "regeneration_required")
    })

    $Selected = @($Candidates | Where-Object {
        $_.state -eq "approved_for_staging_candidate"
    })

    foreach ($Candidate in $Ready) {
        if (-not $Candidate.local_preview_path -or -not (Test-Path $Candidate.local_preview_path)) {
            $Problems.Add("Ready candidate missing preview file: $($Candidate.name)")
        }

        if ($Candidate.publish_allowed -ne $false) {
            $Problems.Add("Ready candidate publish_allowed is not false: $($Candidate.name)")
        }
    }

    # -----------------------------
    # 4. Dashboard API.
    # -----------------------------

    $DashboardOk = $false
    $ApiReady = $null
    $ApiRenderer = $null
    $ApiRepair = $null

    try {
        $Api = Invoke-WebRequest "http://127.0.0.1:8788/api/nothingbuta/factory-review" -UseBasicParsing -TimeoutSec 8
        $ApiJson = $Api.Content | ConvertFrom-Json

        if ($ApiJson.state -eq "review_pipeline_ready") {
            $DashboardOk = $true
            $ApiReady = $ApiJson.counts.ready_for_chris_review
            $ApiRenderer = $ApiJson.counts.renderer_needed
            $ApiRepair = $ApiJson.counts.repair_queue
        }
        else {
            $Problems.Add("Dashboard API did not return review_pipeline_ready.")
        }
    }
    catch {
        $Problems.Add("Dashboard API check failed: $($_.Exception.Message)")
    }

    # -----------------------------
    # 5. Candidate folders and script size.
    # -----------------------------

    $PreviewFolders = @()

    if (Test-Path $CandidatesDir) {
        $PreviewFolders = @(Get-ChildItem $CandidatesDir -Directory)
    }
    else {
        $Problems.Add("Candidates directory missing: $CandidatesDir")
    }

    $FactoryLineCount = (Get-Content $FactoryPyPath).Count

    if ($FactoryLineCount -gt 150) {
        $Problems.Add("Factory script is oversized at $FactoryLineCount lines. Module split is recommended before more renderer packs.")
    }

    $AuditStatus = if ($Problems.Count -eq 0) { "pass" } else { "warn" }
    $IsoNow = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")

    $Audit = [pscustomobject]@{
        audit_id = "nothingbuta-overnight-factory-audit"
        created_at = $IsoNow
        status = $AuditStatus
        task = @{
            last_run_time = $TaskInfo.LastRunTime
            last_task_result = $TaskInfo.LastTaskResult
            next_run_time = $TaskInfo.NextRunTime
            missed_runs = $TaskInfo.NumberOfMissedRuns
            minutes_since_last_run = $MinutesSinceLastRun
        }
        latest_factory = @{
            run_id = $LatestFactory.run_id
            status = $LatestFactory.status
            built_count = @($LatestFactory.built_candidates).Count
            backlog_candidate_count = $LatestFactory.backlog_candidate_count
        }
        counts = @{
            ready_100_score = $Ready.Count
            renderer_needed = $RendererNeeded.Count
            repair_needed = $RepairNeeded.Count
            selected_for_staging = $Selected.Count
            total_candidates = $Candidates.Count
            registry_generated = $Generated.Count
            preview_folders = $PreviewFolders.Count
        }
        dashboard = @{
            api_ok = $DashboardOk
            ready_for_chris_review = $ApiReady
            renderer_needed = $ApiRenderer
            repair_queue = $ApiRepair
        }
        script_risk = @{
            factory_script_lines = $FactoryLineCount
            module_split_recommended = ($FactoryLineCount -gt 150)
        }
        safety = @{
            commit_allowed = $false
            push_allowed = $false
            publish_allowed = $false
            analytics_allowed = $false
            ads_allowed = $false
            affiliate_links_allowed = $false
            lead_capture_allowed = $false
        }
        problems = @($Problems.ToArray())
        next_recommended_gate = "local_factory_module_split"
    }

    Write-CleanText -Path $AuditJsonPath -Value ($Audit | ConvertTo-Json -Depth 12)

    $ProblemText = if ($Problems.Count -eq 0) {
        "- None"
    }
    else {
        ($Problems | ForEach-Object { "- $_" }) -join "`n"
    }

    $Report = @"
# NothingButA Overnight Factory Audit

Generated: $IsoNow

## Status

$($AuditStatus.ToUpper())

## Scheduled Task

- Last run: $($TaskInfo.LastRunTime)
- Last result: $($TaskInfo.LastTaskResult)
- Next run: $($TaskInfo.NextRunTime)
- Missed runs: $($TaskInfo.NumberOfMissedRuns)
- Minutes since last run: $MinutesSinceLastRun

## Latest Factory Run

- Run ID: $($LatestFactory.run_id)
- Status: $($LatestFactory.status)
- Built this run: $(@($LatestFactory.built_candidates).Count)
- Backlog candidates: $($LatestFactory.backlog_candidate_count)

## Candidate Counts

- Ready 100-score candidates: $($Ready.Count)
- Needs renderer: $($RendererNeeded.Count)
- Needs repair: $($RepairNeeded.Count)
- Selected for staging: $($Selected.Count)
- Total candidates: $($Candidates.Count)
- Registry generated: $($Generated.Count)
- Preview folders: $($PreviewFolders.Count)

## Dashboard API

- API OK: $DashboardOk
- Ready: $ApiReady
- Renderer needed: $ApiRenderer
- Repair queue: $ApiRepair

## Script Size

- Factory script lines: $FactoryLineCount
- Module split recommended: $($FactoryLineCount -gt 150)

## Problems / Warnings

$ProblemText

## Safety

- Commit: disabled
- Push: disabled
- Publish: disabled
- GitHub Pages changes: disabled
- Analytics: disabled
- Ads: disabled
- Affiliate links: disabled
- Lead capture: disabled

## Next Recommended Gate

I approve local Factory Module Split
"@

    Write-CleanText -Path $AuditMdPath -Value $Report

    Write-Host "`nNOTHINGBUTA OVERNIGHT FACTORY AUDIT: $($AuditStatus.ToUpper())" -ForegroundColor Cyan
    Write-Host "Ready 100-score: $($Ready.Count)"
    Write-Host "Needs renderer:  $($RendererNeeded.Count)"
    Write-Host "Needs repair:    $($RepairNeeded.Count)"
    Write-Host "Preview folders: $($PreviewFolders.Count)"
    Write-Host "Task result:     $($TaskInfo.LastTaskResult)"
    Write-Host "Missed runs:     $($TaskInfo.NumberOfMissedRuns)"
    Write-Host "Script lines:    $FactoryLineCount"
    Write-Host "Report:          $AuditMdPath"

    if ($Problems.Count -gt 0) {
        Write-Host "`nWarnings:" -ForegroundColor Yellow
        $Problems | ForEach-Object { Write-Host "- $_" -ForegroundColor Yellow }
    }
}
catch {
    Write-Host "`nNOTHINGBUTA OVERNIGHT FACTORY AUDIT: FAIL" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}