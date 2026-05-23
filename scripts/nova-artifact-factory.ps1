$ErrorActionPreference = "Stop"

function Write-FactoryLog {
    param([string]$Message, [string]$Level = "INFO")
    Write-Host "[Artifact Factory][$Level] $Message"
}

function Set-Prop {
    param($Object, [string]$Name, $Value)

    if ($Object.PSObject.Properties.Name -contains $Name) {
        $Object.$Name = $Value
    }
    else {
        $Object | Add-Member -MemberType NoteProperty -Name $Name -Value $Value
    }
}

try {
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $dataDir = Join-Path $workspace "data"
    $reviewsRoot = Join-Path $workspace "money_scout\internet_reviews"
    $reportsDir = Join-Path $workspace "reports"

    New-Item -ItemType Directory -Force -Path $dataDir, $reviewsRoot, $reportsDir | Out-Null

    $inboxPath = Join-Path $dataDir "internet_idea_inbox.json"
    $registryPath = Join-Path $dataDir "artifact_registry.json"
    $reportPath = Join-Path $reportsDir "artifact-factory-report.md"

    if (-not (Test-Path $inboxPath)) {
        throw "Missing inbox: $inboxPath"
    }

    if (-not (Test-Path $registryPath)) {
        [pscustomobject]@{
            schema_version = "1.0"
            updated_at = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
            artifacts = @()
        } | ConvertTo-Json -Depth 20 | Set-Content -Path $registryPath -Encoding UTF8
    }

    $backupStamp = Get-Date -Format yyyyMMdd-HHmmss
    Copy-Item $registryPath "$registryPath.bak-$backupStamp"

    $inbox = Get-Content $inboxPath -Raw | ConvertFrom-Json
    $registry = Get-Content $registryPath -Raw | ConvertFrom-Json

    if (-not ($registry.PSObject.Properties.Name -contains "artifacts")) {
        $registry | Add-Member -MemberType NoteProperty -Name artifacts -Value @()
    }

    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
    $created = 0
    $skipped = 0
    $report = @("# Artifact Factory Report", "", "Generated At: $now", "")

    $readyIdeas = @($inbox.ideas | Where-Object { $_.status -eq "review_ready" })

    foreach ($idea in $readyIdeas) {
        $existing = @($registry.artifacts | Where-Object { $_.idea_id -eq $idea.idea_id }).Count

        if ($existing -gt 0) {
            $skipped += 1
            $report += "- Skipped existing artifact for $($idea.idea_id): $($idea.title)"
            continue
        }

        $artifactId = "artifact-$($idea.idea_id)-001"
        $artifactDir = Join-Path $reviewsRoot "$($idea.idea_id)\artifact_draft"
        New-Item -ItemType Directory -Force -Path $artifactDir | Out-Null

        $metadataPath = Join-Path $artifactDir "artifact_metadata.json"
        $outlinePath = Join-Path $artifactDir "artifact_outline.md"
        $packetPath = Join-Path $artifactDir "review_packet.md"

        $title = "Local Review Artifact - $($idea.title)"

        $metadata = [pscustomobject]@{
            schema_version = "1.0"
            artifact_id = $artifactId
            idea_id = $idea.idea_id
            status = "local_draft_only"
            created_at = $now
            title = $title
            source_url = $idea.source_url
            evidence_quality = $idea.evidence_quality
            approval_required_before = @(
                "publishing",
                "selling",
                "outreach",
                "commit",
                "push",
                "live_site_change",
                "spending",
                "claiming_compliance",
                "legal_advice"
            )
            safety_note = "Review artifact only. Not legal advice. Does not prove buyer demand or revenue."
        }

        $metadata | ConvertTo-Json -Depth 20 | Set-Content -Path $metadataPath -Encoding UTF8

        $outline = @"
# $title

Status: Local draft only  
Idea ID: $($idea.idea_id)  
Generated at: $now

## Safety

This is not legal advice.  
This is not a compliance guarantee.  
This does not prove buyer demand or revenue.  
This must not be published, sold, committed, pushed, or used for outreach without Chris approval.

## Source-Backed Claim

$($idea.claim_supported)

## Audience

$($idea.audience)

## Pain Point

$($idea.pain_point)

## Draft Asset Concept

$($idea.proposed_solution)

## Local Draft Sections

1. Problem summary
2. Evidence summary
3. Risk notes
4. Checklist or worksheet outline
5. Local test idea
6. Chris review decision

## Chris Review Decision

- approve for local test
- revise
- park
- reject
"@

        $outline | Set-Content -Path $outlinePath -Encoding UTF8

        $packet = @"
# Review Packet: $artifactId

Generated at: $now

## Artifact

- Idea: $($idea.idea_id)
- Title: $title
- Status: local_draft_only

## Evidence Basis

$($idea.evidence_summary)

## What This Proves

The system can convert a review-ready source-backed signal into a local draft artifact.

## What This Does Not Prove

- Buyer demand
- Revenue
- Legal correctness
- Compliance certainty

## Approval Gates

No publishing, selling, outreach, commits, pushes, live changes, spending, credential use, or compliance claims without Chris approval.
"@

        $packet | Set-Content -Path $packetPath -Encoding UTF8

        $registry.artifacts = @($registry.artifacts) + [pscustomobject]@{
            artifact_id = $artifactId
            idea_id = $idea.idea_id
            status = "local_draft_only"
            title = $title
            created_at = $now
            path = $artifactDir
            approval_required_before = $metadata.approval_required_before
        }

        $created += 1
        $report += "- Created $artifactId for $($idea.idea_id): $($idea.title)"
    }

    Set-Prop -Object $registry -Name "updated_at" -Value $now
    $registry | ConvertTo-Json -Depth 30 | Set-Content -Path $registryPath -Encoding UTF8

    $report += ""
    $report += "## Totals"
    $report += ""
    $report += "- Review-ready ideas: $(@($readyIdeas).Count)"
    $report += "- Created: $created"
    $report += "- Skipped existing: $skipped"
    $report += ""
    $report += "## Safety"
    $report += ""
    $report += "No external action performed."

    $report | Set-Content -Path $reportPath -Encoding UTF8

    Write-FactoryLog "Created artifacts: $created"
    Write-FactoryLog "Skipped existing: $skipped"
    Write-FactoryLog "Registry: $registryPath"
    Write-FactoryLog "Report: $reportPath"
}
catch {
    Write-Error "[Artifact Factory] FAILED: $($_.Exception.Message)"
    exit 1
}
