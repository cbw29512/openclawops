function Write-ScoutLog {
    param([string]$Message, [string]$Level = "INFO")
    Write-Host "[Internet Auto Discover V2][$Level] $Message"
}

function Get-NormalizedUrl {
    param([string]$Url)

    if ([string]::IsNullOrWhiteSpace($Url)) {
        return ""
    }

    try {
        $uri = [Uri]$Url.Trim()
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

        return $builder.Uri.AbsoluteUri.TrimEnd("/")
    }
    catch {
        return $Url.Trim().ToLowerInvariant()
    }
}

function Get-TitleFingerprint {
    param([string]$Title)

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
    param([string]$Title, [string]$Url)

    $inputText = "$(Get-TitleFingerprint $Title)|$(Get-NormalizedUrl $Url)"
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($inputText)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $hash = $sha.ComputeHash($bytes)

    return ([BitConverter]::ToString($hash)).Replace("-", "").ToLowerInvariant()
}

function Convert-ToPlainText {
    param($Value)

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

function Get-AtomLink {
    param($Entry)

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

function Get-FeedItems {
    param([xml]$Xml)

    $items = @()

    if ($Xml.rss.channel.item) {
        foreach ($item in @($Xml.rss.channel.item)) {
            $items += [pscustomobject]@{
                title = Convert-ToPlainText $item.title
                link = Convert-ToPlainText $item.link
                description = Convert-ToPlainText $item.description
                feed_format = "rss"
            }
        }

        return $items
    }

    if ($Xml.feed.entry) {
        foreach ($entry in @($Xml.feed.entry)) {
            $items += [pscustomobject]@{
                title = Convert-ToPlainText $entry.title
                link = Get-AtomLink $entry
                description = Convert-ToPlainText $entry.summary
                feed_format = "atom"
            }
        }

        return $items
    }

    return @()
}

function Get-NextIdeaId {
    param($Inbox)

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

function Test-TermMatch {
    param([string]$Text, [string[]]$Terms)

    foreach ($term in $Terms) {
        if ($Text -match [regex]::Escape($term.ToLowerInvariant())) {
            return $true
        }
    }

    return $false
}

function Get-OpportunityScore {
    param([string]$Title, [string]$Summary)

    $text = "$Title $Summary".ToLowerInvariant()

    $buyerTerms = @("small business", "client", "customer", "paid", "pricing", "buy", "sales", "revenue", "budget", "owner", "freelancer", "agency", "shopify", "webflow", "woo", "pos", "taxes")
    $painTerms = @("problem", "help", "struggle", "need", "looking for", "can't", "manual", "takes too long", "expensive", "workflow", "spam", "waste", "hard", "stuck", "done with", "behind")
    $monetizationTerms = @("affiliate", "template", "course", "newsletter", "lead", "saas", "tool", "prompt", "checklist", "service", "landing page", "product", "database", "subscribe")
    $testabilityTerms = @("template", "checklist", "prompt", "landing page", "workflow", "tool", "guide", "audit", "review", "generator", "script", "database", "app")
    $noiseTerms = @("lawsuit", "acquires", "acquisition", "pope", "encyclical", "co-founder", "radio stations", "lost his lawsuit", "press release")

    $buyer = if (Test-TermMatch -Text $text -Terms $buyerTerms) { 2 } else { 0 }
    $pain = if (Test-TermMatch -Text $text -Terms $painTerms) { 2 } else { 0 }
    $monetization = if (Test-TermMatch -Text $text -Terms $monetizationTerms) { 2 } else { 0 }
    $testability = if (Test-TermMatch -Text $text -Terms $testabilityTerms) { 2 } else { 0 }
    $evidence = if ([string]::IsNullOrWhiteSpace($Summary)) { 0 } else { 2 }
    $noise = if (Test-TermMatch -Text $text -Terms $noiseTerms) { 3 } else { 0 }

    $total = $buyer + $pain + $monetization + $testability + $evidence - $noise

    return [pscustomobject]@{
        buyer_signal = $buyer
        pain_signal = $pain
        monetization_signal = $monetization
        testability_signal = $testability
        evidence_quality = $evidence
        noise_penalty = $noise
        total = $total
    }
}

function Ensure-ArrayProperty {
    param($Object, [string]$Name)

    if (-not ($Object.PSObject.Properties.Name -contains $Name)) {
        $Object | Add-Member -MemberType NoteProperty -Name $Name -Value @()
    }
}
