$ErrorActionPreference = "Stop"

function Write-RunnerLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )

    # Runner logs are intentionally simple so Chris can spot failures fast.
    Write-Host "[Nova Startup Runner][$Level] $Message"
}

function Read-RequiredFile {
    param(
        [string]$Path,
        [string]$Label
    )

    # Fail closed: Nova must never receive fake state if a required file is missing.
    if (-not (Test-Path $Path)) {
        throw "Missing required file for $Label`: $Path"
    }

    # Read the exact file contents from disk.
    return Get-Content -Path $Path -Raw
}

try {
    # State root for Nova's local operating files.
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"

    # Required state files.
    $statusPath = Join-Path $workspace "CURRENT_STATUS.md"
    $approvalPolicyPath = Join-Path $workspace "APPROVAL_POLICY.md"
    $tasksPath = Join-Path $workspace "data\tasks.json"
    $approvalQueuePath = Join-Path $workspace "data\approval_queue.json"

    # Logs folder stores generated prompt packets for proof/review.
    $logsDir = Join-Path $workspace "logs"

    if (-not (Test-Path $logsDir)) {
        New-Item -ItemType Directory -Path $logsDir | Out-Null
    }

    # Read actual disk state.
    $currentStatus = Read-RequiredFile -Path $statusPath -Label "current status"
    $approvalPolicy = Read-RequiredFile -Path $approvalPolicyPath -Label "approval policy"
    $tasksJson = Read-RequiredFile -Path $tasksPath -Label "tasks"
    $approvalQueueJson = Read-RequiredFile -Path $approvalQueuePath -Label "approval queue"

    # Timestamp gives each startup packet a proof marker.
    $generatedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

    # Build the prompt packet Nova will receive.
    # Important: this packet includes real file contents, so Nova no longer needs file access.
    $packet = @"
NOVA VERIFIED STARTUP PACKET

Generated At:
$generatedAt

Workspace Path:
$workspace

Critical Rule:
You did not read these files yourself. PowerShell read them and injected the verified contents below.
Do not claim direct file access unless Chris separately proves that capability.

Operating Format:
For every task, respond with:
1. Current State
2. Problem
3. Safest Next Action
4. Exact Command or File Change
5. Proof Needed

Approval Gates:
You must ask Chris before spending money, publishing, uploading, sending messages, performing outreach, creating accounts, using credentials, changing affiliate links, committing code, pushing to GitHub, modifying live production pages, deleting important files, running destructive commands, or taking external actions.

===== CURRENT_STATUS.md =====
$currentStatus

===== APPROVAL_POLICY.md =====
$approvalPolicy

===== tasks.json =====
$tasksJson

===== approval_queue.json =====
$approvalQueueJson

Task:
Summarize the verified startup state.
Identify the active task.
Identify any blocked or risky actions.
Recommend the safest next local-only action.

Required final line:
NOVA_VERIFIED_STARTUP_READY
"@

    # Save the exact prompt packet to disk for auditability.
    $packetPath = Join-Path $logsDir ("nova-startup-packet-{0}.txt" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
    Set-Content -Path $packetPath -Value $packet -Encoding UTF8

    # Copy to clipboard so Chris can paste it directly into the OpenClaw TUI.
    Set-Clipboard -Value $packet

    Write-RunnerLog "Startup packet generated."
    Write-RunnerLog "Saved packet to: $packetPath"
    Write-RunnerLog "Copied packet to clipboard."
    Write-RunnerLog "Paste into Nova's OpenClaw TUI now."
}
catch {
    Write-Error "[Nova Startup Runner] FAILED: $($_.Exception.Message)"
    exit 1
}
