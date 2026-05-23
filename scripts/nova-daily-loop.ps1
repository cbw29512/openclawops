$ErrorActionPreference = "Stop"

function Write-NovaLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )

    # Keep logs simple so Chris can immediately see what succeeded or failed.
    Write-Host "[Nova Daily Loop][$Level] $Message"
}

function Read-RequiredTextFile {
    param(
        [string]$Path,
        [string]$Label
    )

    # Fail closed: do not give Nova fake state if a required file is missing.
    if (-not (Test-Path $Path)) {
        throw "Missing required $Label file: $Path"
    }

    # Read exact disk contents so Nova receives verified state.
    return Get-Content -Path $Path -Raw
}

function Ensure-JsonFile {
    param(
        [string]$Path,
        [string]$DefaultJson,
        [string]$Label
    )

    # Create missing JSON state files with known-safe defaults.
    if (-not (Test-Path $Path)) {
        Set-Content -Path $Path -Value $DefaultJson -Encoding UTF8
        Write-NovaLog "Created missing $Label file: $Path"
    }

    # Validate JSON early so Nova does not receive corrupted state.
    try {
        Get-Content -Path $Path -Raw | ConvertFrom-Json | Out-Null
    }
    catch {
        throw "$Label contains invalid JSON: $Path"
    }
}

try {
    # State root.
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"

    # State folders.
    $dataDir = Join-Path $workspace "data"
    $logsDir = Join-Path $workspace "logs"
    $dailyDir = Join-Path $workspace "daily"

    foreach ($dir in @($workspace, $dataDir, $logsDir, $dailyDir)) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir | Out-Null
        }
    }

    # Required files.
    $statusPath = Join-Path $workspace "CURRENT_STATUS.md"
    $approvalPolicyPath = Join-Path $workspace "APPROVAL_POLICY.md"
    $tasksPath = Join-Path $dataDir "tasks.json"
    $approvalQueuePath = Join-Path $dataDir "approval_queue.json"
    $workLogPath = Join-Path $dataDir "work_log.json"

    # Baseline JSON files if missing.
    Ensure-JsonFile `
        -Path $tasksPath `
        -Label "tasks" `
        -DefaultJson '{"schema_version":"1.0","tasks":[]}'

    Ensure-JsonFile `
        -Path $approvalQueuePath `
        -Label "approval queue" `
        -DefaultJson '{"schema_version":"1.0","approvals":[]}'

    Ensure-JsonFile `
        -Path $workLogPath `
        -Label "work log" `
        -DefaultJson '{"schema_version":"1.0","entries":[]}'

    # Required markdown files.
    $currentStatus = Read-RequiredTextFile -Path $statusPath -Label "current status"
    $approvalPolicy = Read-RequiredTextFile -Path $approvalPolicyPath -Label "approval policy"

    # Required JSON content.
    $tasksJson = Read-RequiredTextFile -Path $tasksPath -Label "tasks"
    $approvalQueueJson = Read-RequiredTextFile -Path $approvalQueuePath -Label "approval queue"
    $workLogJson = Read-RequiredTextFile -Path $workLogPath -Label "work log"

    # Timestamps for auditability.
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $generatedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

    # Build the verified packet.
    $packet = @"
NOVA DAILY LOCAL WORK LOOP PACKET

Generated At:
$generatedAt

Workspace:
$workspace

Critical Rule:
PowerShell read the files below. Nova did not directly read local files.
Do not claim direct file access.
Do not perform external actions.
Do not delete files.
Do not connect channels.
Do not spend, publish, upload, message, commit, push, or modify live systems without Chris approval.

Required Response Format:
1. Current State
2. Active Tasks
3. Blocked / Risky Actions
4. Safest Next Local-Only Action
5. Exact Command or File Change
6. Proof Needed

===== CURRENT_STATUS.md =====
$currentStatus

===== APPROVAL_POLICY.md =====
$approvalPolicy

===== tasks.json =====
$tasksJson

===== approval_queue.json =====
$approvalQueueJson

===== work_log.json =====
$workLogJson

Task:
Review the verified local state.
Identify the active task.
Identify risks or approval-gated actions.
Recommend the safest next local-only step.
Do not invent completed work.

Required final line:
NOVA_DAILY_LOOP_READY
"@

    # Save packet for proof.
    $packetPath = Join-Path $logsDir "nova-daily-loop-packet-$stamp.txt"
    Set-Content -Path $packetPath -Value $packet -Encoding UTF8

    # Save a simple daily report stub.
    $dailyReportPath = Join-Path $dailyDir "daily-report-$stamp.md"

@"
# Nova Daily Report

Generated At: $generatedAt

## Status

Daily packet generated and copied to clipboard.

## Packet

$packetPath

## Next Step

Paste the packet into Nova's OpenClaw TUI and confirm the response ends with:

NOVA_DAILY_LOOP_READY
"@ | Set-Content -Path $dailyReportPath -Encoding UTF8

    # Copy packet to clipboard for paste into Nova.
    Set-Clipboard -Value $packet

    Write-NovaLog "Daily packet generated."
    Write-NovaLog "Packet saved to: $packetPath"
    Write-NovaLog "Daily report saved to: $dailyReportPath"
    Write-NovaLog "Packet copied to clipboard."
    Write-NovaLog "Paste into Nova now with Ctrl+V."
}
catch {
    Write-Error "[Nova Daily Loop] FAILED: $($_.Exception.Message)"
    exit 1
}
