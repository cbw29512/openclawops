$ErrorActionPreference = "Stop"

function Write-PacketLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )

    # These logs show whether the packet was generated and copied.
    Write-Host "[PushButton QA Packet][$Level] $Message"
}

try {
    # Root folders.
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $moneyDir = Join-Path $workspace "money_scout"
    $experimentDir = Join-Path $moneyDir "experiments\exp-0001"
    $logsDir = Join-Path $workspace "logs"

    # Required experiment files.
    $activeExperimentPath = Join-Path $moneyDir "active_experiment.json"
    $qaPath = Join-Path $experimentDir "qa_checklist.json"
    $evidencePath = Join-Path $experimentDir "evidence_packet.md"
    $nextActionsPath = Join-Path $experimentDir "next_actions.md"

    foreach ($file in @($activeExperimentPath, $qaPath, $evidencePath, $nextActionsPath)) {
        if (-not (Test-Path $file)) {
            throw "Missing required file: $file"
        }
    }

    # Read and validate structured state.
    $activeExperiment = Get-Content $activeExperimentPath -Raw | ConvertFrom-Json
    $qa = Get-Content $qaPath -Raw | ConvertFrom-Json

    if ($activeExperiment.idea_id -ne "ms-0002") {
        throw "Expected active idea ms-0002, found: $($activeExperiment.idea_id)"
    }

    if ($qa.status -ne "research_only") {
        throw "Expected QA status research_only, found: $($qa.status)"
    }

    # Build compact checklist summary instead of dumping the whole file.
    $checkLines = @($qa.checks | ForEach-Object {
        "- $($_.check_id) | $($_.area) | status=$($_.status) | approval_required=$($_.approval_required) | question=$($_.question)"
    })

    $notCheckedCount = @($qa.checks | Where-Object { $_.status -eq "not_checked" }).Count
    $approvalCount = @($qa.checks | Where-Object { $_.approval_required -eq $true }).Count

    $generatedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"

    # Compact packet keeps Nova focused and protects the local context window.
    $packetLines = @(
        "NOVA PUSHBUTTONTOOLS QA REVIEW PACKET",
        "",
        "Generated At:",
        $generatedAt,
        "",
        "Critical Rules:",
        "PowerShell read the local files and injected this compact packet.",
        "Nova must not claim direct file access.",
        "Nova must not invent evidence.",
        "Nova must not claim revenue, conversion lift, or demand is proven.",
        "Nova must not perform external actions.",
        "Chris approval is required before publishing, outreach, live changes, commits, pushes, affiliate changes, spending, or credential use.",
        "",
        "Active Experiment:",
        "experiment_id: $($activeExperiment.experiment_id)",
        "idea_id: $($activeExperiment.idea_id)",
        "title: $($activeExperiment.title)",
        "status: $($activeExperiment.status)",
        "next_safe_action: $($activeExperiment.next_safe_action)",
        "",
        "QA Checklist Summary:",
        "total_checks: $(@($qa.checks).Count)",
        "not_checked: $notCheckedCount",
        "approval_required_checks: $approvalCount",
        "",
        "Checks:",
        ($checkLines -join "`r`n"),
        "",
        "Task for Nova:",
        "Review this QA checklist.",
        "Confirm whether it is safe and useful for the first local-only evidence pass.",
        "Pick the first evidence item Chris should collect.",
        "Do not suggest changing the live site.",
        "Do not suggest committing, pushing, publishing, outreach, spending, or affiliate changes.",
        "",
        "Required Response Format:",
        "1. Current State",
        "2. QA Checklist Readiness",
        "3. Anti-Hallucination Risks",
        "4. First Evidence Item to Collect",
        "5. Exact Local-Only Next Step",
        "6. Proof Needed",
        "",
        "Required final line:",
        "NOVA_PUSHBUTTON_QA_READY"
    )

    $packet = $packetLines -join "`r`n"
    $packetPath = Join-Path $logsDir "nova-pushbutton-qa-packet-$stamp.txt"

    Set-Content -Path $packetPath -Value $packet -Encoding UTF8
    Set-Clipboard -Value $packet

    Write-PacketLog "Created compact PushButtonTools QA packet."
    Write-PacketLog "Saved to: $packetPath"
    Write-PacketLog "Copied to clipboard."
    Write-PacketLog "Paste into Nova money-scout TUI."
}
catch {
    Write-Error "[PushButton QA Packet] FAILED: $($_.Exception.Message)"
    exit 1
}
