$ErrorActionPreference = "Stop"

function Write-RepairLog {
    param([string]$Message, [string]$Level = "INFO")
    Write-Host "[Weak Summary Repair][$Level] $Message"
}

function Set-Prop {
    param(
        [Parameter(Mandatory = $true)] $Object,
        [Parameter(Mandatory = $true)] [string] $Name,
        [Parameter(Mandatory = $true)] $Value
    )

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
    $moneyDir = Join-Path $workspace "money_scout"

    $inboxPath = Join-Path $dataDir "internet_idea_inbox.json"

    if (-not (Test-Path $inboxPath)) {
        throw "Missing inbox file: $inboxPath"
    }

    $inbox = Get-Content $inboxPath -Raw | ConvertFrom-Json
    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

    $weakIdeas = @(
        $inbox.ideas |
            Where-Object { $_.evidence_summary -eq "Comments" }
    )

    if ($weakIdeas.Count -eq 0) {
        Write-RepairLog "No weak 'Comments' summaries found."
        exit 0
    }

    Copy-Item $inboxPath "$inboxPath.bak-$(Get-Date -Format yyyyMMdd-HHmmss)"
    Write-RepairLog "Found weak summaries: $($weakIdeas.Count)"

    foreach ($idea in $weakIdeas) {
        $ideaId = [string]$idea.idea_id
        $title = [string]$idea.title
        $sourceUrl = [string]$idea.source_url

        if ([string]::IsNullOrWhiteSpace($ideaId)) {
            Write-RepairLog "Skipping item with blank idea_id." "WARN"
            continue
        }

        $reviewDir = Join-Path $moneyDir "internet_reviews\$ideaId"
        New-Item -ItemType Directory -Force -Path $reviewDir | Out-Null

        $reviewPath = Join-Path $reviewDir "source_review.md"

        Set-Prop -Object $idea -Name "status" -Value "source_review_required"
        Set-Prop -Object $idea -Name "evidence_quality" -Value "weak_parser_summary_repaired"
        Set-Prop -Object $idea -Name "confidence" -Value "low"
        Set-Prop -Object $idea -Name "evidence_summary" -Value "Parser produced weak summary value 'Comments'. This item is preserved for dedupe/source review only. Title and URL may indicate a possible opportunity, but no buyer demand, revenue, conversion, or safe action is proven. Source review is required before promotion."
        Set-Prop -Object $idea -Name "source_reviewed_at" -Value $now
        Set-Prop -Object $idea -Name "source_review_result" -Value "weak_parser_summary_repaired_keep_source_review_required"
        Set-Prop -Object $idea -Name "score_reason" -Value "Weak parser summary repaired automatically without promotion."

        $riskFlags = @($idea.risk_flags)

        foreach ($flag in @(
            "weak parser summary repaired",
            "source review required",
            "no buyer demand proof",
            "no revenue proof",
            "no promotion",
            "no external action allowed"
        )) {
            if ($riskFlags -notcontains $flag) {
                $riskFlags += $flag
            }
        }

        Set-Prop -Object $idea -Name "risk_flags" -Value $riskFlags

        $review = @"
# Source Review: $ideaId

Generated At: $now

## Title

$title

## Source URL

$sourceUrl

## Repair Reason

The parser produced the weak summary value:

Comments

That value is not usable evidence.

## Safe Repair

The item was kept as source_review_required and given a non-promotional repaired summary.

## What This Does Not Prove

- It does not prove buyer demand.
- It does not prove revenue.
- It does not prove conversion.
- It does not prove Nova should build, sell, publish, or contact anyone.
- It does not allow external action.

## Required Next Step

A real source review is required before this idea can be promoted.
"@

        Set-Content -Path $reviewPath -Value $review -Encoding UTF8
        Write-RepairLog "Repaired weak summary: $ideaId"
    }

    Set-Prop -Object $inbox -Name "updated_at" -Value $now

    $inbox | ConvertTo-Json -Depth 60 | Set-Content -Path $inboxPath -Encoding UTF8

    # Validate JSON after writing so the hourly cycle fails loudly if something corrupts.
    Get-Content $inboxPath -Raw | ConvertFrom-Json | Out-Null

    Write-RepairLog "Weak summary repair complete."
}
catch {
    Write-Error "[Weak Summary Repair] FAILED: $($_.Exception.Message)"
    exit 1
}
