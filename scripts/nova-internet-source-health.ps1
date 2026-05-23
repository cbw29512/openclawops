$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    Write-Host "[Source Health][$Level] $Message"
}

function Get-NodeText {
    param($Node)

    try {
        if ($null -eq $Node) {
            return ""
        }

        if ($Node -is [System.Xml.XmlElement]) {
            return ([string]$Node.InnerText).Trim()
        }

        return ([string]$Node).Trim()
    }
    catch {
        return ""
    }
}

function Get-AtomLink {
    param($Entry)

    try {
        foreach ($link in @($Entry.link)) {
            if ($link.rel -eq "alternate" -and $link.href) {
                return ([string]$link.href).Trim()
            }
        }

        foreach ($link in @($Entry.link)) {
            if ($link.href) {
                return ([string]$link.href).Trim()
            }
        }

        return ""
    }
    catch {
        return ""
    }
}

try {
    $workspace = Join-Path $env:USERPROFILE "OpenClawOps"
    $reportsDir = Join-Path $workspace "reports"

    New-Item -ItemType Directory -Force -Path $reportsDir | Out-Null

    $jsonPath = Join-Path $reportsDir "internet-source-health.json"
    $mdPath = Join-Path $reportsDir "internet-source-health.md"

    $sources = @(
        [pscustomobject]@{ name = "Hacker News RSS"; url = "https://news.ycombinator.com/rss" },
        [pscustomobject]@{ name = "Reddit Entrepreneur RSS"; url = "https://www.reddit.com/r/Entrepreneur/new/.rss" },
        [pscustomobject]@{ name = "Reddit SideProject RSS"; url = "https://www.reddit.com/r/SideProject/new/.rss" },
        [pscustomobject]@{ name = "Reddit SmallBusiness RSS"; url = "https://www.reddit.com/r/smallbusiness/new/.rss" }
    )

    $results = @()

    foreach ($source in $sources) {
        Write-Log "Checking $($source.name)"

        $result = [pscustomobject]@{
            name = $source.name
            url = $source.url
            reachable = $false
            feed_format = "unknown"
            items_found = 0
            sample_titles = @()
            sample_links = @()
            error = ""
        }

        try {
            $response = Invoke-WebRequest `
                -Uri $source.url `
                -UseBasicParsing `
                -Headers @{ "User-Agent" = "NovaMoneyScout/1.0 source health auditor" } `
                -TimeoutSec 20

            $result.reachable = $true

            [xml]$xml = $response.Content

            if ($xml.rss.channel.item) {
                $result.feed_format = "rss"
                $items = @($xml.rss.channel.item)
                $result.items_found = $items.Count

                foreach ($item in ($items | Select-Object -First 5)) {
                    $result.sample_titles += Get-NodeText $item.title
                    $result.sample_links += Get-NodeText $item.link
                }
            }
            elseif ($xml.feed.entry) {
                $result.feed_format = "atom"
                $items = @($xml.feed.entry)
                $result.items_found = $items.Count

                foreach ($entry in ($items | Select-Object -First 5)) {
                    $result.sample_titles += Get-NodeText $entry.title
                    $result.sample_links += Get-AtomLink $entry
                }
            }
            else {
                $result.error = "Reachable, but parser found neither rss.channel.item nor feed.entry."
            }
        }
        catch {
            $result.error = $_.Exception.Message
        }

        $results += $result
    }

    $summary = [pscustomobject]@{
        generated_at = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
        sources_checked = @($results).Count
        reachable = @($results | Where-Object { $_.reachable -eq $true }).Count
        total_items_found = (@($results | Measure-Object -Property items_found -Sum).Sum)
        results = $results
    }

    $summary | ConvertTo-Json -Depth 20 | Set-Content -Path $jsonPath -Encoding UTF8

    $md = @()
    $md += "# Internet Source Health"
    $md += ""
    $md += "Generated At: $($summary.generated_at)"
    $md += ""
    $md += "- Sources checked: $($summary.sources_checked)"
    $md += "- Reachable: $($summary.reachable)"
    $md += "- Total items found: $($summary.total_items_found)"
    $md += ""

    foreach ($r in $results) {
        $md += "## $($r.name)"
        $md += ""
        $md += "- URL: $($r.url)"
        $md += "- Reachable: $($r.reachable)"
        $md += "- Feed format: $($r.feed_format)"
        $md += "- Items found: $($r.items_found)"
        $md += "- Error: $($r.error)"
        $md += ""
        $md += "Sample titles:"

        foreach ($title in $r.sample_titles) {
            $md += "- $title"
        }

        $md += ""
    }

    $md | Set-Content -Path $mdPath -Encoding UTF8

    Write-Log "Source health audit complete."
    Write-Log "Markdown: $mdPath"
    Write-Log "JSON: $jsonPath"

    Get-Content $mdPath -TotalCount 120
}
catch {
    Write-Error "[Source Health] FAILED: $($_.Exception.Message)"
    exit 1
}
