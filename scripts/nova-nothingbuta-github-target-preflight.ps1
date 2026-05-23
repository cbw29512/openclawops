try {
    $ErrorActionPreference = "Stop"

    $Root = "C:\Users\dmchris\OpenClawOps"
    $TargetPath = Join-Path $Root "data\nothingbuta_github_target.json"
    $RepoReadyIndexPath = Join-Path $Root "nothingbuta\repo_ready\nothingbuta\docs\nothingbuta\debt-payoff-calculator\index.html"

    foreach ($Path in @($TargetPath, $RepoReadyIndexPath)) {
        if (-not (Test-Path $Path)) {
            throw "Missing GitHub target preflight artifact: $Path"
        }
    }

    $Target = Get-Content $TargetPath -Raw | ConvertFrom-Json
    $GitCommand = Get-Command git -ErrorAction SilentlyContinue

    if ($null -eq $GitCommand) {
        throw "Git is not available on PATH."
    }

    $RepoReadyHash = (Get-FileHash -Path $RepoReadyIndexPath -Algorithm SHA256).Hash

    if ($RepoReadyHash -ne $Target.deploy_sha256) {
        throw "Repo-ready hash does not match target deploy SHA256."
    }

    $LocalCloneExists = Test-Path $Target.local_clone_path

    Write-Host "`nNOTHINGBUTA GITHUB TARGET PREFLIGHT" -ForegroundColor Cyan
    Write-Host "Target repo:       $($Target.repo_url)"
    Write-Host "Local clone path:  $($Target.local_clone_path)"
    Write-Host "Repo-ready file:   $RepoReadyIndexPath"
    Write-Host "Hash:              $RepoReadyHash"
    Write-Host "Git available:     True"
    Write-Host "Local clone exists:$LocalCloneExists"
    Write-Host "GitHub API needed: $($Target.github_api_required)"
    Write-Host "Publish allowed:   $($Target.publish_allowed)"

    if ($Target.publish_allowed -ne $false) {
        throw "Safety failure: publish_allowed should be false."
    }

    if ($LocalCloneExists) {
        $Remote = git -C $Target.local_clone_path remote get-url origin 2>$null
        Write-Host "Existing remote:   $Remote"

        if ($Remote -and $Remote -ne $Target.repo_url) {
            throw "Existing clone remote does not match target repo URL."
        }
    }
    else {
        Write-Host "`nClone is not performed by this preflight." -ForegroundColor Yellow
        Write-Host "When Chris approves clone-only, use:" -ForegroundColor Yellow
        Write-Host "git clone $($Target.repo_url) `"$($Target.local_clone_path)`"" -ForegroundColor Yellow
    }

    Write-Host "`nGITHUB TARGET PREFLIGHT: PASS" -ForegroundColor Green
}
catch {
    Write-Host "`nGITHUB TARGET PREFLIGHT: FAIL" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}