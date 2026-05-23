$ErrorActionPreference = "Stop"

function Write-IntakeLog {
    param([string]$Message, [string]$Level = "INFO")
    Write-Host "[Internet Intake][$Level] $Message"
}

try {
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $dataDir = Join-Path $workspace "data"
    $inboxPath = Join-Path $dataDir "internet_idea_inbox.json"

    New-Item -ItemType Directory -Force -Path $dataDir | Out-Null

    if (-not (Test-Path $inboxPath)) {
        $emptyInbox = [pscustomobject]@{
            schema_version = "1.0"
            updated_at = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
            ideas = @()
        }
        $emptyInbox | ConvertTo-Json -Depth 10 | Set-Content -Path $inboxPath -Encoding UTF8
    }

    $backupPath = "$inboxPath.bak-$(Get-Date -Format yyyyMMdd-HHmmss)"
    Copy-Item $inboxPath $backupPath
    Write-IntakeLog "Backup created: $backupPath"

    $inbox = Get-Content $inboxPath -Raw | ConvertFrom-Json

    if (-not ($inbox.PSObject.Properties.Name -contains "ideas")) {
        $inbox | Add-Member -MemberType NoteProperty -Name ideas -Value @()
    }

    $existingCount = @($inbox.ideas).Count
    $nextNumber = $existingCount + 1
    $ideaId = "web-{0:D4}" -f $nextNumber

    Write-Host ""
    Write-Host "Add Internet Money Idea"
    Write-Host "Evidence only. No external action."
    Write-Host ""

    $title = Read-Host "Idea title"
    $sourceUrl = Read-Host "Source URL"
    $claimSupported = Read-Host "What claim does this source actually support?"
    $evidenceSummary = Read-Host "Evidence summary"
    $audience = Read-Host "Audience"
    $painPoint = Read-Host "Pain point"
    $solution = Read-Host "Proposed tiny test / solution"
    $monetization = Read-Host "Monetization model"
    $riskFlagsText = Read-Host "Risk flags, comma separated"

    if ([string]::IsNullOrWhiteSpace($title)) { throw "Idea title cannot be blank." }
    if ([string]::IsNullOrWhiteSpace($sourceUrl)) { throw "Source URL cannot be blank. No source, no evidence." }
    if ([string]::IsNullOrWhiteSpace($claimSupported)) { throw "claim_supported cannot be blank." }
    if ([string]::IsNullOrWhiteSpace($evidenceSummary)) { throw "evidence_summary cannot be blank." }

    $riskFlags = @()
    if (-not [string]::IsNullOrWhiteSpace($riskFlagsText)) {
        $riskFlags = @($riskFlagsText.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    }

    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

    $newIdea = [pscustomobject]@{
        idea_id = $ideaId
        status = "evidence_pending"
        title = $title
        source_url = $sourceUrl
        source_type = "manual_url"
        claim_supported = $claimSupported
        evidence_summary = $evidenceSummary
        audience = $audience
        pain_point = $painPoint
        proposed_solution = $solution
        monetization_model = $monetization
        confidence = "low"
        created_at = $now
        risk_flags = $riskFlags
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

    $inbox.ideas = @($inbox.ideas) + $newIdea

    if (-not ($inbox.PSObject.Properties.Name -contains "updated_at")) {
        $inbox | Add-Member -MemberType NoteProperty -Name updated_at -Value $now
    }
    else {
        $inbox.updated_at = $now
    }

    $inbox | ConvertTo-Json -Depth 20 | Set-Content -Path $inboxPath -Encoding UTF8
    Get-Content $inboxPath -Raw | ConvertFrom-Json | Out-Null

    Write-IntakeLog "Added idea: $ideaId"
    Write-IntakeLog "Status: evidence_pending"
    Write-IntakeLog "Inbox: $inboxPath"
}
catch {
    Write-Error "[Internet Intake] FAILED: $($_.Exception.Message)"
    exit 1
}
