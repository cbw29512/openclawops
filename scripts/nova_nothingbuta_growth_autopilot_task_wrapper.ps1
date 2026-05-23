try {
    $ErrorActionPreference = "Stop"

    $Root = "C:\Users\dmchris\OpenClawOps"
    $LogPath = Join-Path $Root "reports\nothingbuta-growth-autopilot-task.log"
    $V1Script = Join-Path $Root "scripts\nova_nothingbuta_growth_autopilot_v1.py"
    $V2Script = Join-Path $Root "scripts\nova_nothingbuta_traffic_intelligence_v2.py"

    Add-Content -Path $LogPath -Value ""
    Add-Content -Path $LogPath -Value "---- Growth Autopilot task run started: $(Get-Date -Format s) ----"

    Set-Location $Root

    python $V1Script *>> $LogPath
    $V1Exit = $LASTEXITCODE

    python $V2Script *>> $LogPath
    $V2Exit = $LASTEXITCODE

    if ($V1Exit -ne 0) {
        $ExitCode = $V1Exit
    }
    elseif ($V2Exit -ne 0) {
        $ExitCode = $V2Exit
    }
    else {
        $ExitCode = 0
    }

    Add-Content -Path $LogPath -Value "---- Growth Autopilot task run finished: $(Get-Date -Format s), v1=$V1Exit, v2=$V2Exit, exit=$ExitCode ----"

    exit $ExitCode
}
catch {
    $Root = "C:\Users\dmchris\OpenClawOps"
    $LogPath = Join-Path $Root "reports\nothingbuta-growth-autopilot-task.log"

    Add-Content -Path $LogPath -Value "---- Growth Autopilot task wrapper failed: $(Get-Date -Format s) ----"
    Add-Content -Path $LogPath -Value $_.Exception.Message

    exit 1
}
