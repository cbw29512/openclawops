try {
    $ErrorActionPreference = "Stop"

    $Root = "C:\Users\dmchris\OpenClawOps"

    $PlanPath = Join-Path $Root "data\nothingbuta_publish_target_plan.json"
    $ManifestPath = Join-Path $Root "nothingbuta\deploy_packages\nba-util-0001-v1\deploy-manifest.json"
    $DeployPath = Join-Path $Root "nothingbuta\deploy_packages\nba-util-0001-v1\index.html"

    foreach ($Path in @($PlanPath, $ManifestPath, $DeployPath)) {
        if (-not (Test-Path $Path)) {
            throw "Missing preflight artifact: $Path"
        }
    }

    $Plan = Get-Content $PlanPath -Raw | ConvertFrom-Json
    $Manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
    $DeployHash = (Get-FileHash -Path $DeployPath -Algorithm SHA256).Hash

    if ($Plan.state -ne "publish_target_plan_ready") {
        throw "Publish target plan is not ready."
    }

    if ($Manifest.state -ne "deploy_package_ready") {
        throw "Deploy manifest is not ready."
    }

    if ($DeployHash -ne $Manifest.deploy_sha256) {
        throw "Deploy hash mismatch. Re-freeze and re-package before publishing."
    }

    if ($Plan.publish_allowed -ne $false) {
        throw "Safety failure: publish_allowed should still be false."
    }

    Write-Host "`nNOTHINGBUTA PUBLISH PREFLIGHT: PASS" -ForegroundColor Green
    Write-Host "Release: $($Plan.release_id)"
    Write-Host "Host:    $($Plan.recommended_host)"
    Write-Host "Path:    $($Plan.recommended_public_path)"
    Write-Host "Publish: $($Plan.publish_allowed)"
}
catch {
    Write-Host "`nNOTHINGBUTA PUBLISH PREFLIGHT: FAIL" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}