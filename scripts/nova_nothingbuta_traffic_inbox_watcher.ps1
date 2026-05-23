try {
    $ErrorActionPreference = "Stop"

    $Root = "C:\Users\dmchris\OpenClawOps"
    $Inbox = Join-Path $Root "data\nothingbuta_traffic_inbox"
    $LogPath = Join-Path $Root "reports\nothingbuta-traffic-inbox-watcher.log"
    $TrafficScript = Join-Path $Root "scripts\nova_nothingbuta_traffic_intelligence_v2.py"

    Add-Content -Path $LogPath -Value ""
    Add-Content -Path $LogPath -Value "---- Traffic inbox watcher started: $(Get-Date -Format s) ----"

    $CsvFiles = Get-ChildItem -Path $Inbox -Filter "*.csv" -File -ErrorAction SilentlyContinue

    if (-not $CsvFiles -or $CsvFiles.Count -eq 0) {
        Add-Content -Path $LogPath -Value "No CSV files found. Waiting for Search Console export."
        Add-Content -Path $LogPath -Value "---- Traffic inbox watcher finished: $(Get-Date -Format s), exit=0 ----"
        exit 0
    }

    Add-Content -Path $LogPath -Value "CSV files found: $($CsvFiles.Count)"

    Set-Location $Root

    python $TrafficScript *>> $LogPath
    $ExitCode = $LASTEXITCODE

    Add-Content -Path $LogPath -Value "Traffic Intelligence exit code: $ExitCode"
    Add-Content -Path $LogPath -Value "---- Traffic inbox watcher finished: $(Get-Date -Format s), exit=$ExitCode ----"

    exit $ExitCode
}
catch {
    $Root = "C:\Users\dmchris\OpenClawOps"
    $LogPath = Join-Path $Root "reports\nothingbuta-traffic-inbox-watcher.log"

    Add-Content -Path $LogPath -Value "---- Traffic inbox watcher failed: $(Get-Date -Format s) ----"
    Add-Content -Path $LogPath -Value $_.Exception.Message

    exit 1
}
