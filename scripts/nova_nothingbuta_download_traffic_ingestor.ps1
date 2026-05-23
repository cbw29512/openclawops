try {
    $ErrorActionPreference = "Stop"

    $Root = "C:\Users\dmchris\OpenClawOps"
    $Downloads = Join-Path $env:USERPROFILE "Downloads"
    $Inbox = Join-Path $Root "data\nothingbuta_traffic_inbox"
    $Reports = Join-Path $Root "reports"
    $LogPath = Join-Path $Reports "nothingbuta-download-traffic-ingestor.log"
    $TrafficScript = Join-Path $Root "scripts\nova_nothingbuta_traffic_intelligence_v2.py"

    New-Item -ItemType Directory -Force -Path $Inbox | Out-Null
    New-Item -ItemType Directory -Force -Path $Reports | Out-Null

    Add-Content -Path $LogPath -Value ""
    Add-Content -Path $LogPath -Value "---- Download traffic ingestor started: $(Get-Date -Format s) ----"

    if (-not (Test-Path $Downloads)) {
        throw "Downloads folder missing: $Downloads"
    }

    $Cutoff = (Get-Date).AddDays(-3)

    $Candidates = Get-ChildItem -Path $Downloads -Filter "*.csv" -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -ge $Cutoff } |
        Sort-Object LastWriteTime -Descending

    if (-not $Candidates -or $Candidates.Count -eq 0) {
        Add-Content -Path $LogPath -Value "No recent CSV files found in Downloads."
        Add-Content -Path $LogPath -Value "---- Download traffic ingestor finished: $(Get-Date -Format s), exit=0 ----"
        exit 0
    }

    $Copied = @()

    foreach ($File in $Candidates) {
        try {
            $FirstLine = Get-Content -Path $File.FullName -TotalCount 1 -ErrorAction Stop

            $Header = $FirstLine.ToLowerInvariant()

            $HasUrlColumn =
                $Header.Contains("page") -or
                $Header.Contains("top pages") -or
                $Header.Contains("url") -or
                $Header.Contains("landing page")

            $HasClicks = $Header.Contains("click")
            $HasImpressions = $Header.Contains("impression")
            $HasCtr = $Header.Contains("ctr") -or $Header.Contains("click through")
            $HasPosition = $Header.Contains("position")

            if ($HasUrlColumn -and $HasClicks -and $HasImpressions -and $HasCtr -and $HasPosition) {
                $SafeName = "gsc_" + (Get-Date -Format "yyyyMMdd_HHmmss") + "_" + $File.Name
                $Target = Join-Path $Inbox $SafeName

                Copy-Item -Path $File.FullName -Destination $Target -Force

                $Copied += $Target

                Add-Content -Path $LogPath -Value "Copied valid Search Console CSV:"
                Add-Content -Path $LogPath -Value "  from: $($File.FullName)"
                Add-Content -Path $LogPath -Value "  to:   $Target"
            }
            else {
                Add-Content -Path $LogPath -Value "Skipped CSV without required GSC headers: $($File.Name)"
            }
        }
        catch {
            Add-Content -Path $LogPath -Value "Skipped unreadable CSV: $($File.FullName)"
            Add-Content -Path $LogPath -Value $_.Exception.Message
        }
    }

    if ($Copied.Count -gt 0) {
        Set-Location $Root

        Add-Content -Path $LogPath -Value "Running Traffic Intelligence v2 after ingest..."

        python $TrafficScript *>> $LogPath
        $ExitCode = $LASTEXITCODE

        Add-Content -Path $LogPath -Value "Traffic Intelligence exit code: $ExitCode"
        Add-Content -Path $LogPath -Value "---- Download traffic ingestor finished: $(Get-Date -Format s), copied=$($Copied.Count), exit=$ExitCode ----"

        exit $ExitCode
    }

    Add-Content -Path $LogPath -Value "No valid Search Console CSV files copied."
    Add-Content -Path $LogPath -Value "---- Download traffic ingestor finished: $(Get-Date -Format s), exit=0 ----"
    exit 0
}
catch {
    $Root = "C:\Users\dmchris\OpenClawOps"
    $Reports = Join-Path $Root "reports"
    $LogPath = Join-Path $Reports "nothingbuta-download-traffic-ingestor.log"

    New-Item -ItemType Directory -Force -Path $Reports | Out-Null

    Add-Content -Path $LogPath -Value "---- Download traffic ingestor failed: $(Get-Date -Format s) ----"
    Add-Content -Path $LogPath -Value $_.Exception.Message

    exit 1
}
