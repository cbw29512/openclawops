$ErrorActionPreference = "Stop"

function Write-ScoutLog {
    param([string]$Message, [string]$Level = "INFO")
    Write-Host "[Internet Auto Discover][$Level] $Message"
}

function Get-NormalizedUrl {
    param([string]$Url)

    # Normalize URLs so tracking params do not create duplicate ideas.
    if ([string]::IsNullOrWhiteSpace($Url)) {
        return ""
    }

    try {
        $uri = [Uri]$Url.Trim()

        # Drop common tracking query params.
        $queryPairs = @()
        if (-not [string]::IsNullOrWhiteSpace($uri.Query)) {
            $rawQuery = $uri.Query.TrimStart("?").Split("&") | Where-Object { $_ }

            foreach ($pair in $rawQuery) {
                $key = ($pair.Split("=")[0]).ToLowerInvariant()

                if ($key -notmatch "^(utm_|fbclid$|gclid$|mc_cid$|mc_eid$|ref$|ref_src$)") {
                    $queryPairs += $pair
                }
            }
        }

        $builder = [System.UriBuilder]::new($uri)
        $builder.Scheme = $builder.Scheme.ToLowerInvariant()
        $builder.Host = $builder.Host.ToLowerInvariant()
        $builder.Fragment = ""
        $builder.Query = ($queryPairs -join "&")

        # Trim trailing slash for stable comparison.
        return $builder.Uri.AbsoluteUri.TrimEnd("/")
    }
    catch {
        return $Url.Trim().ToLowerInvariant()
    }
}

function Get-TitleFingerprint {
    param([string]$Title)

    # Fingerprint catches repeated story/idea titles across sources.
    if ([string]::IsNullOrWhiteSpace($Title)) {
        return ""
    }

    $value = $Title.ToLowerInvariant()
    $value = $value -replace "[^a-z0-9\s]", " "
    $value = $value -replace "\b(the|a|an|and|or|to|of|for|in|on|with|using|new|how)\b", " "
    $value = $value -replace "\s+", " "
    return $value.Trim()
}

function Get-ContentFingerprint {
    param(
        [string]$Title,
        [string]$Url
    )

    # Hash title fingerprint + normalized URL so we can store compact identity.
    $inputText = "$(Get-TitleFingerprint $Title)|$(Get-NormalizedUrl $Url)"
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($inputText)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $hash = $sha.ComputeHash($bytes)
    return ([BitConverter]::ToString($hash)).Replace("-", "").ToLowerInvariant()
}

function Convert-ToPlainText {
    param($Value)

    # RSS descriptions can be XmlElement objects. InnerText prevents System.Xml.XmlElement pollution.
    if ($null -eq $Value) {
        return ""
    }

    if ($Value -is [System.Xml.XmlElement]) {
        $text = $Value.InnerText
    }
    else {
        $text = [string]$Value
    }

    if ([string]::IsNullOrWhiteSpace($text)) {
        return ""
    }

    return ($text -replace "<[^>]+>", " " -replace "\s+", " ").Trim()
}

function Get-NextIdeaId {
    param($Inbox)

    # Finds the highest existing web-#### number and increments it.
    $max = 0

    foreach ($idea in @($Inbox.ideas)) {
        if ($idea.idea_id -match "^web-(\d+)$") {
            $num = [int]$Matches[1]
            if ($num -gt $max) {
                $max = $num
            }
        }
    }

    return "web-{0:D4}" -f ($max + 1)
}

function Ensure-Registry {
    param([string]$RegistryPath)

    if (-not (Test-Path $RegistryPath)) {
        [pscustomobject]@{
            schema_version = "1.0"
            updated_at = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
            seen_urls = @()
            title_fingerprints = @()
            content_fingerprints = @()
            history = @()
        } | ConvertTo-Json -Depth 20 | Set-Content -Path $RegistryPath -Encoding UTF8
    }

    return Get-Content $RegistryPath -Raw | ConvertFrom-Json
}

try {
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $dataDir = Join-Path $workspace "data"
    $logsDir = Join-Path $workspace "logs"

    $inboxPath = Join-Path $dataDir "internet_idea_inbox.json"
    $registryPath = Join-Path $dataDir "internet_seen_registry.json"

    New-Item -ItemType Directory -Force -Path $dataDir, $logsDir | Out-Null

    if (-not (Test-Path $inboxPath)) {
        [pscustomobject]@{
            schema_version = "1.0"
            updated_at = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
            ideas = @()
        } | ConvertTo-Json -Depth 20 | Set-Content -Path $inboxPath -Encoding UTF8
    }

    $inboxBackup = "$inboxPath.bak-$(Get-Date -Format yyyyMMdd-HHmmss)"
    Copy-Item $inboxPath $inboxBackup

    $inbox = Get-Content $inboxPath -Raw | ConvertFrom-Json
    $registry = Ensure-Registry -RegistryPath $registryPath

    if (-not ($inbox.PSObject.Properties.Name -contains "ideas")) {
        $inbox | Add-Member -MemberType NoteProperty -Name ideas -Value @()
    }

    foreach ($prop in @("seen_urls", "title_fingerprints", "content_fingerprints", "history")) {
        if (-not ($registry.PSObject.Properties.Name -contains $prop)) {
            $registry | Add-Member -MemberType NoteProperty -Name $prop -Value @()
        }
    }

    # Backfill registry from current inbox before scanning.
    foreach ($idea in @($inbox.ideas)) {
        $normalizedUrl = Get-NormalizedUrl $idea.source_url
        $titleFingerprint = Get-TitleFingerprint $idea.title
        $contentFingerprint = Get-ContentFingerprint -Title $idea.title -Url $idea.source_url

        if ($normalizedUrl -and (@($registry.seen_urls) -notcontains $normalizedUrl)) {
            $registry.seen_urls = @($registry.seen_urls) + $normalizedUrl
        }

        if ($titleFingerprint -and (@($registry.title_fingerprints) -notcontains $titleFingerprint)) {
            $registry.title_fingerprints = @($registry.title_fingerprints) + $titleFingerprint
        }

        if ($contentFingerprint -and (@($registry.content_fingerprints) -notcontains $contentFingerprint)) {
            $registry.content_fingerprints = @($registry.content_fingerprints) + $contentFingerprint
        }
    }

    $sources = @(
        [pscustomobject]@{ name = "Hacker News RSS"; url = "https://news.ycombinator.com/rss" },
        [pscustomobject]@{ name = "Reddit Entrepreneur RSS"; url = "https://www.reddit.com/r/Entrepreneur/new/.rss" },
        [pscustomobject]@{ name = "Reddit SideProject RSS"; url = "https://www.reddit.com/r/SideProject/new/.rss" },
        [pscustomobject]@{ name = "Reddit SmallBusiness RSS"; url = "https://www.reddit.com/r/smallbusiness/new/.rss" }
    )

    $keywords = @(
        "AI", "automation", "tool", "landing page", "affiliate", "template",
        "small business", "creator", "content", "side project", "SaaS",
        "pricing", "newsletter", "prompt", "workflow", "problem", "help"
    )

    $added = 0
    $checked = 0
    $skippedDuplicate = 0
    $skippedNoMatch = 0
    $failures = @()

    foreach ($source in $sources) {
        try {
            Write-ScoutLog "Checking source: $($source.name)"

            # -UseBasicParsing avoids the old PowerShell parsing warning.
            $response = Invoke-WebRequest `
                -Uri $source.url `
                -UseBasicParsing `
                -Headers @{ "User-Agent" = "NovaMoneyScout/1.0 local evidence collector" } `
                -TimeoutSec 20

            [xml]$rss = $response.Content
            $items = @($rss.rss.channel.item)

            foreach ($item in $items | Select-Object -First 20) {
                $checked += 1

                $title = Convert-ToPlainText $item.title
                $link = Convert-ToPlainText $item.link
                $description = Convert-ToPlainText $item.description

                if ([string]::IsNullOrWhiteSpace($title) -or [string]::IsNullOrWhiteSpace($link)) {
                    continue
                }

                $normalizedUrl = Get-NormalizedUrl $link
                $titleFingerprint = Get-TitleFingerprint $title
                $contentFingerprint = Get-ContentFingerprint -Title $title -Url $link

                $isDuplicate =
                    (@($registry.seen_urls) -contains $normalizedUrl) -or
                    (@($registry.title_fingerprints) -contains $titleFingerprint) -or
                    (@($registry.content_fingerprints) -contains $contentFingerprint)

                if ($isDuplicate) {
                    $skippedDuplicate += 1
                    continue
                }

                $haystack = "$title $description"
                $matched = @($keywords | Where-Object { $haystack -match [regex]::Escape($_) })

                if ($matched.Count -eq 0) {
                    $skippedNoMatch += 1
                    continue
                }

                $ideaId = Get-NextIdeaId -Inbox $inbox
                $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

                $idea = [pscustomobject]@{
                    idea_id = $ideaId
                    status = "raw_discovery"
                    title = $title
                    source_url = $link
                    normalized_url = $normalizedUrl
                    source_name = $source.name
                    source_type = "rss_auto_discovery"
                    claim_supported = "A public feed item matched opportunity keywords: $($matched -join ', '). This does not prove demand or revenue."
                    evidence_summary = $description.Substring(0, [Math]::Min(300, $description.Length))
                    audience = "unknown"
                    pain_point = "unknown until reviewed"
                    proposed_solution = "pending AI review"
                    monetization_model = "unknown"
                    confidence = "low"
                    created_at = $now
                    matched_keywords = $matched
                    title_fingerprint = $titleFingerprint
                    content_fingerprint = $contentFingerprint
                    risk_flags = @("unverified source", "no revenue proof", "requires evidence review")
                    approval_required_before = @(
                        "spending",
                        "publishing",
                        "outreach",
                        "account_creation",
                        "affiliate_link_change",
                        "commit",
                        "push",
                        "live_site_change"
                    )
                }

                $inbox.ideas = @($inbox.ideas) + $idea

                $registry.seen_urls = @($registry.seen_urls) + $normalizedUrl
                $registry.title_fingerprints = @($registry.title_fingerprints) + $titleFingerprint
                $registry.content_fingerprints = @($registry.content_fingerprints) + $contentFingerprint
                $registry.history = @($registry.history) + [pscustomobject]@{
                    idea_id = $ideaId
                    title = $title
                    source_url = $link
                    normalized_url = $normalizedUrl
                    title_fingerprint = $titleFingerprint
                    content_fingerprint = $contentFingerprint
                    first_seen_at = $now
                    source_name = $source.name
                }

                $added += 1
            }
        }
        catch {
            $failures += "$($source.name): $($_.Exception.Message)"
        }
    }

    $nowFinal = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
    $inbox.updated_at = $nowFinal
    $registry.updated_at = $nowFinal

    $inbox | ConvertTo-Json -Depth 30 | Set-Content -Path $inboxPath -Encoding UTF8
    $registry | ConvertTo-Json -Depth 30 | Set-Content -Path $registryPath -Encoding UTF8

    Get-Content $inboxPath -Raw | ConvertFrom-Json | Out-Null
    Get-Content $registryPath -Raw | ConvertFrom-Json | Out-Null

    $logPath = Join-Path $logsDir ("internet-auto-discover-{0}.txt" -f (Get-Date -Format "yyyyMMdd-HHmmss"))

    @"
Internet Auto Discover Run

Checked items: $checked
Added ideas: $added
Skipped duplicates: $skippedDuplicate
Skipped no keyword match: $skippedNoMatch

Failures:
$($failures -join "`r`n")

Inbox:
$inboxPath

Registry:
$registryPath
"@ | Set-Content -Path $logPath -Encoding UTF8

    Write-ScoutLog "Checked items: $checked"
    Write-ScoutLog "Added ideas: $added"
    Write-ScoutLog "Skipped duplicates: $skippedDuplicate"
    Write-ScoutLog "Skipped no keyword match: $skippedNoMatch"
    Write-ScoutLog "Inbox updated: $inboxPath"
    Write-ScoutLog "Registry updated: $registryPath"
    Write-ScoutLog "Run log: $logPath"
}
catch {
    Write-Error "[Internet Auto Discover] FAILED: $($_.Exception.Message)"
    exit 1
}
